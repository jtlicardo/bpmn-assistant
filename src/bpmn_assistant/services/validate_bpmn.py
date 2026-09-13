from pydantic import ValidationError

from bpmn_assistant.core.enums import BPMNElementType
from bpmn_assistant.core.schemas import BPMNPool, BPMNTask, ExclusiveGateway, InclusiveGateway, ParallelGateway
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
        if not is_top_level or any(element.get('type') != 'pool' for element in process):
            raise ValueError('Use either top-level pools or a plain process; do not mix them.')
        validate_pools(process)
        return
    seen_ids = set()
    start_event_count = 0

    for element in process:
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

    supported_elements = [e.value for e in BPMNElementType]

    if element["type"] not in supported_elements:
        raise ValueError(
            f"Unsupported element type: {element['type']}. Supported types: {supported_elements}"
        )

    if element["type"] in [
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

    def reserve(identifier):
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError(f'Duplicate or invalid BPMN ID: {identifier}')
        seen.add(identifier)

    for pool in pools:
        BPMNPool.model_validate(pool)
        reserve(pool['id'])
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
        node_ids = {node['id'] for node in transformed['elements']}
        for node in transformed['elements']:
            reserve(node['id'])
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
                raise ValueError('Sequence flows must stay within their pool; message flows are not supported yet.')
