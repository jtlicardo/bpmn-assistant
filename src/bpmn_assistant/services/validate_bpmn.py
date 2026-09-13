from pydantic import ValidationError

from bpmn_assistant.core.enums import BPMNElementType
from bpmn_assistant.core.schemas import (
    Association, BPMNEvent, BPMNPool, BPMNTask, ExclusiveGateway,
    InclusiveGateway, ParallelGateway, TextAnnotation,
)
from bpmn_assistant.services.element_details import ARTIFACT_TYPES, DETAIL_FIELDS, REFERENCE_TYPES, is_link
from bpmn_assistant.services.bpmn_process_transformer import BpmnProcessTransformer
from bpmn_assistant.services.pools import has_pools


def validate_bpmn(process: list, is_top_level: bool = True) -> None:
    """
    Validate the BPMN process.
    Args:
        process: The BPMN process in JSON format.
        is_top_level: Whether this is the top-level process (not a branch).
    Raises:
        ValueError: If the BPMN process, or any of its elements, is invalid.
    """
    if not isinstance(process, list):
        raise ValueError('Process must be an array.')
    if has_pools(process):
        if not is_top_level or any(element.get('type') not in {'pool', *ARTIFACT_TYPES} for element in process):
            raise ValueError('Use either top-level pools or a plain process; do not mix them. Annotations may accompany pools.')
        validate_pools(process)
        return
    seen_ids = set()
    start_event_count = 0

    for element in process:
        if element.get('type') in ARTIFACT_TYPES and not is_top_level:
            raise ValueError('Place annotations and associations at the process level, outside branches.')
        validate_element(element)

        if element["id"] in seen_ids:
            raise ValueError(f"Duplicate element ID found: {element['id']}")
        seen_ids.add(element["id"])

        # Count start events at the top level
        if is_top_level and element["type"] == BPMNElementType.START_EVENT.value:
            start_event_count += 1

        if element["type"] == BPMNElementType.EXCLUSIVE_GATEWAY.value:
            for branch in element["branches"]:
                validate_bpmn(branch["path"], is_top_level=False)
        if element["type"] == BPMNElementType.INCLUSIVE_GATEWAY.value:
            for branch in element["branches"]:
                validate_bpmn(branch["path"], is_top_level=False)
        if element["type"] == BPMNElementType.PARALLEL_GATEWAY.value:
            for branch in element["branches"]:
                validate_bpmn(branch, is_top_level=False)

    # Check for exactly one start event at the top level
    if is_top_level and start_event_count != 1:
        raise ValueError(f"Process must contain exactly one start event, found {start_event_count}")
    if is_top_level and not _process_has_end_event(process):
        raise ValueError("Process must contain at least one end event")
    if is_top_level:
        # Ensure the process can be transformed into BPMN XML
        transformer = BpmnProcessTransformer()
        transformer.transform(process)
        validate_details(process)


def validate_element(element: dict) -> None:
    """
    Validate the BPMN element.
    Args:
        element: The BPMN element in JSON format.
    Raises:
        ValueError: If the BPMN element is invalid.
    """
    if "id" not in element:
        raise ValueError(f"Element is missing an ID: {element}")
    elif "type" not in element:
        raise ValueError(f"Element is missing a type: {element}")

    supported_elements = [e.value for e in BPMNElementType] + list(ARTIFACT_TYPES)

    if element["type"] not in supported_elements:
        raise ValueError(
            f"Unsupported element type: {element['type']}. Supported types: {supported_elements}"
        )

    if element['type'] == 'textAnnotation':
        TextAnnotation.model_validate(element)
    elif element['type'] == 'association':
        Association.model_validate(element)
    elif element['type'].endswith('Event'):
        BPMNEvent.model_validate(element)
        _validate_event(element)
    elif element["type"] in [
        BPMNElementType.TASK.value,
        BPMNElementType.USER_TASK.value,
        BPMNElementType.SERVICE_TASK.value,
        BPMNElementType.SEND_TASK.value,
        BPMNElementType.RECEIVE_TASK.value,
        BPMNElementType.BUSINESS_RULE_TASK.value,
        BPMNElementType.MANUAL_TASK.value,
        BPMNElementType.SCRIPT_TASK.value,
    ]:
        _validate_task(element)

    elif element["type"] == BPMNElementType.EXCLUSIVE_GATEWAY.value:
        _validate_exclusive_gateway(element)

    elif element["type"] == BPMNElementType.INCLUSIVE_GATEWAY.value:
        _validate_inclusive_gateway(element)

    elif element["type"] == BPMNElementType.PARALLEL_GATEWAY.value:
        _validate_parallel_gateway(element)

    if element.get('loop') is not None and not element['type'].lower().endswith('task'):
        raise ValueError('Loop and multi-instance markers belong on tasks.')
    if not element['type'].endswith('Event') and any(
        element.get(field) is not None for field in ('eventDefinition', *DETAIL_FIELDS[1:])
    ):
        raise ValueError('Event details belong on events.')


def _validate_event(element):
    allowed = {
        'startEvent': {'timer', 'message', 'signal', 'conditional'},
        'endEvent': {'message', 'signal', 'error', 'escalation', 'terminate', 'compensate'},
        'intermediateThrowEvent': {'message', 'signal', 'escalation', 'link', 'compensate'},
        'intermediateCatchEvent': {'timer', 'message', 'signal', 'conditional', 'link'},
    }
    definition = element.get('eventDefinition')
    if definition and definition.removesuffix('EventDefinition') not in allowed[element['type']]:
        raise ValueError(f"Invalid event definition {definition} for {element['type']}.")
    for field, required_definition in (
        ('condition', 'conditionalEventDefinition'), ('link_name', 'linkEventDefinition'),
        ('activity_ref', 'compensateEventDefinition'), ('wait_for_completion', 'compensateEventDefinition'),
    ):
        if element.get(field) is not None and definition != required_definition:
            raise ValueError(f'{field} requires {required_definition}.')
    if definition == 'conditionalEventDefinition' and not (element.get('condition') or '').strip():
        raise ValueError('Conditional events require a condition.')
    if definition == 'linkEventDefinition' and not (element.get('link_name') or '').strip():
        raise ValueError('Link events require a link_name.')
    if element.get('event_reference') and definition not in REFERENCE_TYPES:
        raise ValueError('This event type does not support event_reference.')
    if (element.get('event_reference') or {}).get('code') is not None and definition not in (
        'errorEventDefinition', 'escalationEventDefinition',
    ):
        raise ValueError('Only error and escalation references support a code.')


def validate_details(process):
    """Validate artifact references and event links within a single process."""
    transformed = BpmnProcessTransformer().transform(process)
    nodes = {node['id']: node for node in transformed['elements']}
    artifacts = [item for item in process if item['type'] in ARTIFACT_TYPES]
    seen = set(nodes)
    seen.update(flow['id'] for flow in transformed['flows'])
    seen.update(f"{node['eventDefinition']}_{node['id']}" for node in nodes.values() if node.get('eventDefinition'))
    for artifact in artifacts:
        if artifact['id'] in seen:
            raise ValueError(f"Duplicate BPMN ID: {artifact['id']}")
        seen.add(artifact['id'])
    for identifier in event_references(nodes.values()):
        if identifier in seen or identifier in ('definitions_1', 'Process_1', 'Collaboration_1'):
            raise ValueError(f'Duplicate BPMN ID: {identifier}')
    validate_associations(artifacts, set(nodes))
    links = {}
    for node in nodes.values():
        if node.get('activity_ref'):
            target = nodes.get(node['activity_ref'])
            if not target or not target['type'].lower().endswith('task'):
                raise ValueError('Compensation activity_ref must reference a task in the same process.')
        if node.get('eventDefinition') == 'linkEventDefinition':
            links.setdefault(node['link_name'], []).append(node)
    for group in links.values():
        if sum(is_link(node, 'intermediateCatchEvent') for node in group) != 1 or sum(
            is_link(node, 'intermediateThrowEvent') for node in group
        ) != 1:
            raise ValueError('Each link name needs exactly one catch and one throw in the same process (layout requirement).')


def event_references(nodes):
    references = {}
    for node in nodes:
        reference = node.get('event_reference')
        if reference:
            value = (REFERENCE_TYPES[node['eventDefinition']][0], reference)
            if reference['id'] in references and references[reference['id']] != value:
                raise ValueError(f"Conflicting event reference: {reference['id']}")
            references[reference['id']] = value
    return references


def validate_associations(artifacts, node_ids):
    annotations = {item['id'] for item in artifacts if item['type'] == 'textAnnotation'}
    for item in artifacts:
        if item['type'] != 'association':
            continue
        endpoints = {item['source_ref'], item['target_ref']}
        if len(endpoints) != 2 or not endpoints <= (node_ids | annotations) or not endpoints & annotations:
            raise ValueError('Annotation associations must connect existing, distinct nodes/annotations in the same scope.')


def _validate_task(element: dict) -> None:
    if "label" not in element:
        raise ValueError(f"Task element is missing a label: {element}")

    try:
        BPMNTask.model_validate(element)
    except ValidationError:
        raise ValueError(f"Invalid task element: {element}")


def _validate_exclusive_gateway(element: dict) -> None:
    if "label" not in element:
        raise ValueError(f"Exclusive gateway is missing a label: {element}")
    if "branches" not in element or not isinstance(element["branches"], list):
        raise ValueError(
            f"Exclusive gateway is missing or has invalid 'branches': {element}"
        )
    branch_paths = []
    for branch in element["branches"]:
        if "condition" not in branch or "path" not in branch:
            raise ValueError(f"Invalid branch in exclusive gateway: {branch}")
        if not isinstance(branch["path"], list):
            raise ValueError(f"Exclusive gateway branch 'path' must be a list: {branch}")
        branch_paths.append(branch["path"])

    if branch_paths and all(len(path) == 0 for path in branch_paths):
        raise ValueError(
            "Exclusive gateway must have at least one branch with elements; all branch paths are empty."
        )

    try:
        ExclusiveGateway.model_validate(element)
    except ValidationError:
        raise ValueError(f"Invalid exclusive gateway element: {element}")


def _validate_inclusive_gateway(element: dict) -> None:
    if "label" not in element:
        raise ValueError(f"Inclusive gateway is missing a label: {element}")
    if "branches" not in element or not isinstance(element["branches"], list):
        raise ValueError(
            f"Inclusive gateway is missing or has invalid 'branches': {element}"
        )
    for branch in element["branches"]:
        # Default branches don't require a condition, but all branches need a path
        if "path" not in branch:
            raise ValueError(f"Invalid branch in inclusive gateway (missing 'path'): {branch}")
        # Non-default branches must have a condition
        if not branch.get("is_default", False) and "condition" not in branch:
            raise ValueError(f"Invalid branch in inclusive gateway (non-default branch missing 'condition'): {branch}")

    try:
        InclusiveGateway.model_validate(element)
    except ValidationError:
        raise ValueError(f"Invalid inclusive gateway element: {element}")


def _validate_parallel_gateway(element: dict) -> None:
    if "branches" not in element or not isinstance(element["branches"], list):
        raise ValueError(
            f"Parallel gateway has missing or invalid 'branches': {element}"
        )

    try:
        ParallelGateway.model_validate(element)
    except ValidationError:
        raise ValueError(f"Invalid parallel gateway element: {element}")

def _process_has_end_event(process: list[dict]) -> bool:
    """Recursively check whether a process (including branches) contains at least one end event."""
    for element in process:
        if element["type"] == BPMNElementType.END_EVENT.value:
            return True
        if element["type"] in [
            BPMNElementType.EXCLUSIVE_GATEWAY.value,
            BPMNElementType.INCLUSIVE_GATEWAY.value
        ]:
            for branch in element["branches"]:
                if _process_has_end_event(branch["path"]):
                    return True
        if element["type"] == BPMNElementType.PARALLEL_GATEWAY.value:
            for branch in element["branches"]:
                if _process_has_end_event(branch):
                    return True
    return False


def validate_pools(pools: list) -> None:
    """Validate pool contents, lane assignments, and diagram-wide IDs."""
    seen = {'definitions_1', 'Collaboration_1'}
    endpoints = {}
    all_nodes = []
    artifacts = [item for item in pools if item.get('type') in ARTIFACT_TYPES]
    pools = [item for item in pools if item.get('type') not in ARTIFACT_TYPES]

    def reserve(identifier):
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError(f'Duplicate or invalid BPMN ID: {identifier}')
        seen.add(identifier)

    for pool in pools:
        BPMNPool.model_validate(pool)
        reserve(pool['id'])
        endpoints[pool['id']] = (pool['id'], 'pool', None)
        reserve(pool['process_id'])
        lanes = pool.get('lanes', [])
        lane_ids = {lane['id'] for lane in lanes}
        if lanes:
            reserve(f"{pool['process_id']}_lanes")
        for lane in lanes:
            reserve(lane['id'])
        contents = pool['process']
        if has_pools(contents):
            raise ValueError('Pools must be top-level containers, not nested inside another pool.')
        if contents:
            validate_bpmn(contents)
        transformed = BpmnProcessTransformer().transform(contents)
        all_nodes.extend(transformed['elements'])
        for artifact in contents:
            if artifact['type'] in ARTIFACT_TYPES:
                reserve(artifact['id'])
        node_ids = {node['id'] for node in transformed['elements']}
        for node in transformed['elements']:
            reserve(node['id'])
            endpoints[node['id']] = (pool['id'], node['type'], node.get('eventDefinition'))
            lane_id = node.get('lane_id')
            if lane_id is not None and lane_id not in lane_ids:
                raise ValueError(f"Element {node['id']} refers to an unknown lane: {lane_id}")
            if lanes and lane_id is None:
                raise ValueError(f"Assign element {node['id']} to a lane in pool {pool['id']}.")
            if node.get('eventDefinition'):
                reserve(f"{node['eventDefinition']}_{node['id']}")
        for flow in transformed['flows']:
            reserve(flow['id'])
            if flow['sourceRef'] not in node_ids or flow['targetRef'] not in node_ids:
                raise ValueError('Sequence flows must stay within their pool; use message flows between pools.')

    for identifier in event_references(all_nodes):
        reserve(identifier)
    for artifact in artifacts:
        validate_element(artifact)
        reserve(artifact['id'])
    validate_associations(artifacts, set(endpoints))
    for pool in pools:
        for flow in pool.get('message_flows', []):
            reserve(flow['id'])
            source = endpoints.get(flow['source_ref'])
            target = endpoints.get(flow['target_ref'])
            if source is None or target is None:
                raise ValueError('Message flow refers to a missing or unsupported endpoint.')
            if source[0] != pool['id']:
                raise ValueError('Store each message flow in its source pool.')
            if source[0] == target[0]:
                raise ValueError('Message flows must connect different pools, not lanes within a pool.')
            for endpoint, sending in ((source, True), (target, False)):
                kind = endpoint[1]
                if endpoint[2] not in (None, 'messageEventDefinition'):
                    raise ValueError('Message flows cannot connect to non-message event definitions.')
                allowed_events = {'endEvent', 'intermediateThrowEvent'} if sending else {'startEvent', 'intermediateCatchEvent'}
                if kind != 'pool' and not kind.lower().endswith('task') and kind not in allowed_events:
                    raise ValueError('Message flows must connect pools, tasks, or events with the correct sending/receiving direction.')
