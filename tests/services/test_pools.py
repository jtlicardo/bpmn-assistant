from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock
import asyncio
import json
import xml.etree.ElementTree as ET

import pytest

from bpmn_assistant import app as api
from bpmn_assistant.api.requests import ModifyBpmnRequest
from bpmn_assistant.core.enums import OutputMode
from bpmn_assistant.core.schemas import ProcessModel
from bpmn_assistant.services import BpmnJsonGenerator, BpmnXmlGenerator, BpmnModelingService
from bpmn_assistant.services.process_editing.bpmn_editing_service import BpmnEditingService
from bpmn_assistant.services.validate_bpmn import validate_bpmn

NS = {'b': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
FIXTURE = Path(__file__).parents[1] / 'fixtures' / 'pools_lanes.bpmn'


@pytest.fixture
def pools():
    return BpmnJsonGenerator().create_bpmn_json(FIXTURE.read_text(encoding='utf-8-sig'))


def test_import_export_preserves_pools_lanes_and_membership(pools):
    assert len(pools) == 2
    assert [lane['label'] for lane in pools[1]['lanes']] == ['Sales', 'Warehouse']
    assert pools[1]['process'][2]['lane_id'] == 'Lane_Warehouse'
    ProcessModel.model_validate({'process': pools})
    xml = BpmnXmlGenerator().create_bpmn_xml(pools)
    root = ET.fromstring(xml)
    assert len(root.findall('./b:collaboration/b:participant', NS)) == 2
    assert root.find('.//b:messageFlow', NS) is None
    assert BpmnJsonGenerator().create_bpmn_json(xml) == pools


def test_join_lane_survives_import_and_export():
    pool = [{
        'type': 'pool', 'id': 'pool', 'process_id': 'proc', 'label': 'Company',
        'lanes': [{'id': 'a', 'label': 'A'}, {'id': 'b', 'label': 'B'}],
        'process': [
            {'type': 'startEvent', 'id': 'start', 'lane_id': 'a'},
            {'type': 'parallelGateway', 'id': 'split', 'lane_id': 'a',
             'join_id': 'custom_join', 'join_lane_id': 'b', 'branches': [
                 [{'type': 'task', 'id': 'one', 'label': 'One', 'lane_id': 'a'}],
                 [{'type': 'task', 'id': 'two', 'label': 'Two', 'lane_id': 'b'}],
             ]},
            {'type': 'endEvent', 'id': 'end', 'lane_id': 'b'},
        ],
    }]
    result = BpmnJsonGenerator().create_bpmn_json(BpmnXmlGenerator().create_bpmn_xml(pool))
    assert result == pool


@pytest.mark.parametrize('change,match', [
    (lambda p: p[1]['process'][2].update(lane_id='missing'), 'unknown lane'),
    (lambda p: p[1]['process'][2].pop('lane_id'), 'Assign element'),
    (lambda p: p[1]['process'][0].update(id=p[0]['process'][0]['id']), 'Duplicate'),
    (lambda p: p[1]['lanes'].append(deepcopy(p[1]['lanes'][0])), 'Duplicate'),
    (lambda p: p.append({'type': 'startEvent', 'id': 'outside'}), 'do not mix'),
    (lambda p: p[0].update(unsupported=[]), 'Extra inputs'),
])
def test_invalid_pool_edits_are_rejected(pools, change, match):
    change(pools)
    with pytest.raises(ValueError, match=match):
        validate_bpmn(pools)


def test_cross_pool_sequence_flow_is_rejected(pools):
    pools[0]['process'].insert(1, {
        'type': 'exclusiveGateway', 'id': 'decision', 'label': 'Continue?', 'has_join': False,
        'branches': [{'condition': 'yes', 'path': [], 'next': 'Supplier_Review'},
                     {'condition': 'no', 'path': [{'type': 'endEvent', 'id': 'stop'}]}],
    })
    with pytest.raises(ValueError, match='stay within their pool'):
        validate_bpmn(pools)


def test_message_flow_import_export_preserves_endpoints_and_label():
    xml = FIXTURE.read_text(encoding='utf-8-sig').replace('</bpmn:collaboration>',
        '<bpmn:messageFlow id="m" sourceRef="Pool_Customer" targetRef="Pool_Supplier" /></bpmn:collaboration>')
    pools = BpmnJsonGenerator().create_bpmn_json(xml)
    assert pools[0]['message_flows'] == [{
        'id': 'm', 'source_ref': 'Pool_Customer', 'target_ref': 'Pool_Supplier', 'label': '',
    }]
    pools[0]['message_flows'][0]['label'] = 'Order & details'
    ProcessModel.model_validate({'process': pools})
    assert BpmnJsonGenerator().create_bpmn_json(BpmnXmlGenerator().create_bpmn_xml(pools)) == pools


def test_nested_lane_import_is_rejected():
    xml = FIXTURE.read_text(encoding='utf-8-sig').replace('<bpmn:lane id="Lane_Sales" name="Sales">',
        '<bpmn:lane id="Lane_Sales" name="Sales"><bpmn:childLaneSet id="nested"/>')
    with pytest.raises(ValueError, match='Nested lanes'):
        BpmnJsonGenerator().create_bpmn_json(xml)


def test_create_and_edit_pools_through_modeling_service(pools):
    llm = Mock()
    llm.call.return_value = {'process': pools}
    service = BpmnModelingService()
    assert service.create_bpmn(llm, []) == pools
    assert 'Pools and lanes' in llm.call.call_args.args[0]
    updated = deepcopy(pools)
    updated[1]['lanes'][0]['label'] = 'Order management'
    updated[1]['process'][2]['lane_id'] = 'Lane_Sales'
    llm.call.side_effect = [
        {'function': 'replace_process', 'arguments': {'process': updated}}, {'stop': True},
    ]
    text_llm = Mock()
    text_llm.call.return_value = 'Rename Sales and move Reserve stock into that lane.'
    result = service.edit_bpmn(llm, text_llm, pools, [])
    assert result == updated
    assert pools[1]['process'][2]['lane_id'] == 'Lane_Warehouse'
    assert BpmnJsonGenerator().create_bpmn_json(BpmnXmlGenerator().create_bpmn_xml(result)) == result


def test_plain_process_can_be_wrapped_in_pool_and_unwrapped(pools):
    plain = deepcopy(pools[0]['process'])
    editor = BpmnEditingService(Mock(), plain, 'Add a customer pool')
    wrapped = editor._update_process(plain, {'function': 'replace_process', 'arguments': {'process': [pools[0]]}})
    assert wrapped == [pools[0]]
    unwrapped = editor._update_process(wrapped, {'function': 'replace_process', 'arguments': {'process': plain}})
    assert unwrapped == plain


def test_modify_api_returns_complete_pool_diagram(pools, monkeypatch):
    llm = Mock()
    llm.call.return_value = {'process': pools}
    monkeypatch.setattr(api, 'get_llm_facade', lambda *args, **kwargs: llm)
    request = ModifyBpmnRequest(message_history=[], process=None, model='test')
    response = asyncio.run(api._modify(request))
    data = json.loads(response.body)
    assert data['bpmn_json'] == pools
    assert BpmnJsonGenerator().create_bpmn_json(data['bpmn_xml']) == pools


def test_empty_pool_can_be_preserved(pools):
    pools.append({'type': 'pool', 'id': 'external', 'process_id': 'external_process',
                  'label': 'External party', 'process': [], 'lanes': []})
    assert BpmnJsonGenerator().create_bpmn_json(BpmnXmlGenerator().create_bpmn_xml(pools)) == pools


def test_modify_api_edits_lane_without_losing_other_pool(pools, monkeypatch):
    changed = deepcopy(pools)
    changed[1]['lanes'][0]['label'] = 'Order management'
    llm = Mock()
    llm.call.side_effect = [
        {'function': 'replace_process', 'arguments': {'process': changed}}, {'stop': True},
    ]
    text_llm = Mock()
    text_llm.call.return_value = 'Rename Sales to Order management.'
    monkeypatch.setattr(api, 'get_llm_facade',
        lambda model, mode=None, **kwargs: text_llm if mode == OutputMode.TEXT else llm)
    request = ModifyBpmnRequest(message_history=[], process=pools, model='test')
    data = json.loads(asyncio.run(api._modify(request)).body)
    assert data['bpmn_json'] == changed
    assert data['bpmn_json'][0] == pools[0]
    assert BpmnJsonGenerator().create_bpmn_json(data['bpmn_xml']) == changed

@pytest.fixture
def message_pools(pools):
    pools[0]['message_flows'] = [{
        'id': 'order_message', 'source_ref': 'Customer_SendOrder',
        'target_ref': 'Supplier_OrderReceived', 'label': 'Purchase order',
    }]
    pools[1]['message_flows'] = [{
        'id': 'confirmation_message', 'source_ref': 'Supplier_Confirm',
        'target_ref': 'Customer_Confirmation', 'label': 'Confirmation',
    }]
    return pools


def test_message_flows_create_edit_and_roundtrip(message_pools):
    llm = Mock()
    llm.call.return_value = {'process': message_pools}
    created = BpmnModelingService().create_bpmn(llm, [])
    xml = BpmnXmlGenerator().create_bpmn_xml(created)
    assert len(ET.fromstring(xml).findall('./b:collaboration/b:messageFlow', NS)) == 2
    assert BpmnJsonGenerator().create_bpmn_json(xml) == message_pools
    changed = deepcopy(message_pools)
    changed[0]['message_flows'][0]['label'] = 'Updated order'
    editor = BpmnEditingService(Mock(), message_pools, 'Rename the message')
    edited = editor._update_process(message_pools, {
        'function': 'replace_process', 'arguments': {'process': changed},
    })
    assert BpmnJsonGenerator().create_bpmn_json(BpmnXmlGenerator().create_bpmn_xml(edited)) == changed
    assert message_pools[0]['message_flows'][0]['label'] == 'Purchase order'
    changed[0]['message_flows'] = []
    validate_bpmn(changed)


@pytest.mark.parametrize('field,value,match', [
    ('target_ref', 'missing', 'missing or unsupported'),
    ('target_ref', 'Customer_Confirmation', 'different pools'),
    ('target_ref', 'Lane_Sales', 'missing or unsupported'),
    ('target_ref', 'Supplier_End', 'sending/receiving'),
    ('source_ref', 'Customer_Start', 'sending/receiving'),
    ('source_ref', 'Supplier_Confirm', 'source pool'),
    ('id', 'Supplier_Confirm', 'Duplicate'),
])
def test_invalid_message_flows_rejected_on_generation_and_import(message_pools, field, value, match):
    xml = BpmnXmlGenerator().create_bpmn_xml(message_pools)
    root = ET.fromstring(xml)
    flow = root.find('./b:collaboration/b:messageFlow', NS)
    flow.set({'source_ref': 'sourceRef', 'target_ref': 'targetRef'}.get(field, field), value)
    # Source ownership is inferred on import, rather than represented in XML.
    if match != 'source pool':
        with pytest.raises(ValueError, match=match):
            BpmnJsonGenerator().create_bpmn_json(ET.tostring(root, encoding='unicode'))
    message_pools[0]['message_flows'][0][field] = value
    with pytest.raises(ValueError, match=match):
        BpmnXmlGenerator().create_bpmn_xml(message_pools)


def test_message_flow_to_empty_pool(message_pools):
    message_pools[1]['process'] = []
    message_pools[1]['lanes'] = []
    message_pools[1].pop('message_flows')
    message_pools[0]['message_flows'][0]['target_ref'] = 'Pool_Supplier'
    xml = BpmnXmlGenerator().create_bpmn_xml(message_pools)
    assert BpmnJsonGenerator().create_bpmn_json(xml) == message_pools


def test_message_flow_rejects_timer_endpoint(message_pools):
    message_pools[1]['process'][0]['eventDefinition'] = 'timerEventDefinition'
    with pytest.raises(ValueError, match='non-message event'):
        validate_bpmn(message_pools)


def test_message_flow_rejects_gateway_endpoint(message_pools):
    message_pools[1]['process'].insert(1, {
        'type': 'parallelGateway', 'id': 'split', 'lane_id': 'Lane_Sales',
        'branches': [
            [{'type': 'task', 'id': 'a', 'label': 'A', 'lane_id': 'Lane_Sales'}],
            [{'type': 'task', 'id': 'b', 'label': 'B', 'lane_id': 'Lane_Sales'}],
        ],
    })
    message_pools[0]['message_flows'][0]['target_ref'] = 'split'
    with pytest.raises(ValueError, match='sending/receiving'):
        validate_bpmn(message_pools)


def test_deleting_message_endpoint_rejects_edit_without_mutating_original(message_pools):
    changed = deepcopy(message_pools)
    changed[0]['process'].pop(1)
    editor = BpmnEditingService(Mock(), message_pools, 'Delete send order')
    with pytest.raises(ValueError, match='missing or unsupported'):
        editor._update_process(message_pools, {
            'function': 'replace_process', 'arguments': {'process': changed},
        })
    assert message_pools[0]['process'][1]['id'] == 'Customer_SendOrder'
