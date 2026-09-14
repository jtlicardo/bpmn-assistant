from bpmn_assistant.services.process_traversal import find_element, walk_elements


def test_locations_preserve_containers_and_scope_boundaries():
    handler = [{'type': 'task', 'id': 'recover'}]
    boundary = {'type': 'boundaryEvent', 'id': 'timeout', 'path': handler, 'next': 'sub'}
    inner = [{'type': 'task', 'id': 'inside'}]
    subprocess = {'type': 'subProcess', 'id': 'sub', 'process': inner,
                  'boundary_events': [boundary]}
    branch = [subprocess]
    contents = [{'type': 'exclusiveGateway', 'id': 'gate',
                 'branches': [{'condition': 'yes', 'path': branch}]}]
    process = [{'type': 'pool', 'id': 'pool', 'process': contents}]

    locations = {location.element['id']: location for location in walk_elements(process)}
    assert list(locations) == ['pool', 'gate', 'sub', 'inside', 'timeout', 'recover']
    assert locations['pool'].scope is process
    assert locations['gate'].scope is contents
    assert locations['sub'].scope is contents
    assert locations['sub'].container is branch
    assert locations['inside'].scope is inner
    assert locations['timeout'].scope is contents
    assert locations['timeout'].container is subprocess['boundary_events']
    assert locations['recover'].scope is contents
    assert locations['recover'].container is handler


def test_lookup_returns_the_actual_list_and_index():
    tasks = [{'type': 'task', 'id': 'first'}, {'type': 'task', 'id': 'second'}]
    process = [{'type': 'parallelGateway', 'id': 'gateway', 'branches': [tasks]}]
    location = find_element(process, 'second')
    assert location.container is tasks
    assert location.index == 1
    assert location.element is tasks[1]
    assert location.scope is process
    assert find_element(process, 'missing') is None
    assert list(walk_elements([])) == []
