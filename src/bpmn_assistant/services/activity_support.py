"""Scope-aware helpers for embedded activities and their exception handlers."""

from bpmn_assistant.services.bpmn_process_transformer import BpmnProcessTransformer
from bpmn_assistant.services.element_details import ARTIFACT_TYPES, is_link


def has_activities(process):
    for item in process:
        if item.get('type') == 'subProcess' or item.get('boundary_events'):
            return True
        if item.get('type') == 'pool' and has_activities(item['process']):
            return True
        for branch in item.get('branches', []):
            if has_activities(branch if isinstance(branch, list) else branch['path']):
                return True
    return False


def scopes(process):
    """Yield each BPMN scope without flattening subprocess interiors into parents."""
    transformed = BpmnProcessTransformer().transform(process)
    yield process, transformed
    for node in transformed['elements']:
        if node['type'] == 'subProcess':
            yield from scopes(node['process'])


def validate_scope_tree(process):
    if not has_activities(process):
        return
    seen = {'definitions_1', 'Process_1', 'Collaboration_1'}
    all_nodes = []

    def reserve(identifier):
        if not identifier or identifier in seen:
            raise ValueError(f'Duplicate or invalid BPMN ID: {identifier}')
        seen.add(identifier)

    for scope, graph in scopes(process):
        all_nodes.extend(graph['elements'])
        nodes = {node['id']: node for node in graph['elements']}
        for node in graph['elements']:
            reserve(node['id'])
            if node.get('eventDefinition'):
                reserve(f"{node['eventDefinition']}_{node['id']}")
        for item in scope:
            if item['type'] in ARTIFACT_TYPES:
                reserve(item['id'])
        if sum(node['type'] == 'startEvent' for node in nodes.values()) != 1:
            raise ValueError('Each scope requires exactly one start; boundary paths cannot contain start events.')
        for flow in graph['flows']:
            reserve(flow['id'])
            if flow['sourceRef'] not in nodes or flow['targetRef'] not in nodes:
                raise ValueError('Sequence flows must stay inside their process or subprocess scope.')
            if nodes[flow['sourceRef']]['type'] == 'endEvent' or nodes[flow['targetRef']]['type'] == 'startEvent':
                raise ValueError('End events cannot have outgoing flows and start events cannot have incoming flows.')
        for node in nodes.values():
            if node['type'] != 'boundaryEvent':
                continue
            host = nodes.get(node['attached_to'])
            if not host or (host['type'] != 'subProcess' and not host['type'].lower().endswith('task')):
                raise ValueError('Boundary event must attach to an activity in the same scope.')
            if node['incoming'] or len(node['outgoing']) != 1:
                raise ValueError('Boundary events require no incoming and exactly one outgoing sequence flow.')
            if node.get('lane_id') != host.get('lane_id'):
                raise ValueError('Boundary events must use the same lane as their host activity.')
            # Every reachable handler exit must terminate or reconnect. Stop at
            # already visited nodes to allow explicit retry loops.
            pending = [node['id']]
            visited = set()
            while pending:
                current = nodes[pending.pop()]
                if current['id'] in visited:
                    continue
                visited.add(current['id'])
                if not current['outgoing'] and current['type'] != 'endEvent' and not is_link(current, 'intermediateThrowEvent'):
                    raise ValueError('Boundary paths must end in an end event or reconnect using next.')
                pending.extend(flow['targetRef'] for flow in graph['flows'] if flow['sourceRef'] == current['id'])
    from bpmn_assistant.services.validate_bpmn import event_references
    if set(event_references(all_nodes)) & seen:
        raise ValueError('Event reference IDs must not collide with diagram element IDs.')
