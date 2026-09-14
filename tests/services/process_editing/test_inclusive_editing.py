from copy import deepcopy

import pytest

from bpmn_assistant.core.exceptions import ElementAlreadyExistsError, ElementNotFoundException
from bpmn_assistant.services.process_editing import (
    add_element, delete_element, move_element, redirect_branch, update_element,
)
from bpmn_assistant.services.process_editing.helpers import get_all_ids
from bpmn_assistant.services.process_editing.bpmn_editing_service import BpmnEditingService


@pytest.fixture
def process():
    return [
        {'type': 'startEvent', 'id': 'start'},
        {'type': 'parallelGateway', 'id': 'parallel', 'branches': [[
            {'type': 'inclusiveGateway', 'id': 'inclusive', 'label': 'Route',
             'has_join': True, 'branches': [
                 {'condition': 'yes', 'path': [
                     {'type': 'task', 'id': 'first', 'label': 'First'},
                     {'type': 'task', 'id': 'second', 'label': 'Second'},
                 ]},
                 {'is_default': True, 'path': []},
             ]},
        ]]},
        {'type': 'endEvent', 'id': 'end'},
    ]


def branch(process):
    return process[1]['branches'][0][0]['branches'][0]


@pytest.mark.parametrize('operation', ['add', 'delete', 'update', 'move', 'redirect'])
def test_edit_inside_nested_inclusive_gateway(process, operation):
    original = deepcopy(process)
    if operation == 'add':
        result = add_element(process, {'type': 'task', 'id': 'new', 'label': 'New'}, before_id='second')
        assert [item['id'] for item in branch(result['process'])['path']] == ['first', 'new', 'second']
    elif operation == 'delete':
        result = delete_element(process, 'first')
        assert [item['id'] for item in branch(result['process'])['path']] == ['second']
    elif operation == 'update':
        result = update_element(process, {'type': 'serviceTask', 'id': 'first', 'label': 'Updated'})
        assert branch(result['process'])['path'][0]['label'] == 'Updated'
    elif operation == 'move':
        result = move_element(process, 'second', before_id='first')
        assert [item['id'] for item in branch(result['process'])['path']] == ['second', 'first']
    else:
        result = redirect_branch(process, 'yes', 'end')
        assert branch(result['process'])['next'] == 'end'
    assert process == original


def test_ids_include_inclusive_children(process):
    assert get_all_ids(process) == ['start', 'parallel', 'inclusive', 'first', 'second', 'end']


def test_add_rejects_id_already_inside_inclusive_branch(process):
    with pytest.raises(ElementAlreadyExistsError):
        add_element(process, {'type': 'task', 'id': 'first', 'label': 'Duplicate'}, after_id='start')


@pytest.mark.parametrize('placement, expected', [
    ({'before_id': 'second'}, ['first', 'second']),
    ({'after_id': 'second'}, ['second', 'first']),
])
def test_move_relocates_after_removing_from_same_list(process, placement, expected):
    result = move_element(process, 'first', **placement)
    assert [item['id'] for item in branch(result['process'])['path']] == expected


def test_failed_move_preserves_input(process):
    original = deepcopy(process)
    with pytest.raises(ElementNotFoundException):
        move_element(process, 'first', before_id='missing')
    assert process == original


@pytest.mark.parametrize('container', [
    {'type': 'pool', 'id': 'pool', 'process': []},
    {'type': 'subProcess', 'id': 'sub', 'process': []},
    {'type': 'task', 'id': 'task', 'boundary_events': [
        {'type': 'boundaryEvent', 'id': 'boundary', 'path': []},
    ]},
])
def test_editor_still_requires_replacement_for_complex_processes(container):
    process = [container]
    editor = BpmnEditingService(None, process, 'Delete the container')
    with pytest.raises(ValueError, match='Use replace_process'):
        editor._update_process(process, {
            'function': 'delete_element', 'arguments': {'element_id': container['id']},
        })
    assert process == [container]
