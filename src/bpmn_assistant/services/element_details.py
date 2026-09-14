"""XML details for events, task repetition, and text annotations."""

import xml.etree.ElementTree as ET


ARTIFACT_TYPES = {'textAnnotation', 'association'}
REFERENCE_TYPES = {
    'signalEventDefinition': ('signal', 'signalRef', None),
    'errorEventDefinition': ('error', 'errorRef', 'errorCode'),
    'escalationEventDefinition': ('escalation', 'escalationRef', 'escalationCode'),
    'messageEventDefinition': ('message', 'messageRef', None),
}
DETAIL_FIELDS = ('loop', 'event_reference', 'condition', 'link_name',
                 'activity_ref', 'wait_for_completion', 'timer')


def is_link(node, kind):
    return node.get('eventDefinition') == 'linkEventDefinition' and node['type'] == kind


def write_event_details(definition, node, root):
    if node.get('timer'):
        timer = node['timer']
        tag = {'duration': 'timeDuration', 'date': 'timeDate', 'cycle': 'timeCycle'}[timer['type']]
        ET.SubElement(definition, tag).text = timer['value']
    reference = node.get('event_reference')
    if reference:
        kind, attribute, code = REFERENCE_TYPES[node['eventDefinition']]
        definition.set(attribute, reference['id'])
        if not any(child.get('id') == reference['id'] for child in root):
            attributes = {'id': reference['id']}
            if reference.get('name') is not None:
                attributes['name'] = reference['name']
            if code and reference.get('code') is not None:
                attributes[code] = reference['code']
            ET.SubElement(root, kind, attributes)
    if node.get('condition') is not None:
        ET.SubElement(definition, 'condition').text = node['condition']
    if node.get('link_name') is not None:
        definition.set('name', node['link_name'])
    if node.get('activity_ref') is not None:
        definition.set('activityRef', node['activity_ref'])
    if node.get('wait_for_completion') is not None:
        definition.set('waitForCompletion', str(node['wait_for_completion']).lower())


def write_loop(element, loop):
    if loop['type'] == 'standard':
        child = ET.SubElement(element, 'standardLoopCharacteristics')
        if loop.get('test_before') is not None:
            child.set('testBefore', str(loop['test_before']).lower())
        if loop.get('maximum') is not None:
            child.set('loopMaximum', str(loop['maximum']))
        if loop.get('condition') is not None:
            ET.SubElement(child, 'loopCondition').text = loop['condition']
    else:
        child = ET.SubElement(element, 'multiInstanceLoopCharacteristics', {
            'isSequential': str(loop['type'] == 'sequential').lower(),
        })
        for field, tag in (('cardinality', 'loopCardinality'),
                           ('completion_condition', 'completionCondition')):
            if loop.get(field) is not None:
                ET.SubElement(child, tag).text = loop[field]


def write_artifacts(process_element, process):
    for item in process:
        if item['type'] == 'textAnnotation':
            annotation = ET.SubElement(process_element, 'textAnnotation', {'id': item['id']})
            ET.SubElement(annotation, 'text').text = item['text']
        elif item['type'] == 'association':
            ET.SubElement(process_element, 'association', {
                'id': item['id'], 'sourceRef': item['source_ref'],
                'targetRef': item['target_ref'], 'associationDirection': item.get('direction', 'None'),
            })


def read_artifacts(process):
    artifacts = []
    for child in process:
        kind = child.tag.split('}')[-1]
        if kind == 'textAnnotation':
            text = child.find('{*}text')
            artifacts.append({'type': kind, 'id': child.get('id'),
                              'text': text.text or '' if text is not None else ''})
        elif kind == 'association':
            artifacts.append({'type': kind, 'id': child.get('id'),
                              'source_ref': child.get('sourceRef'), 'target_ref': child.get('targetRef'),
                              'direction': child.get('associationDirection', 'None')})
    return artifacts


def read_details(element, node, root):
    definitions = [child for child in element if child.tag.endswith('EventDefinition')]
    if len(definitions) > 1:
        raise ValueError('Multiple event definitions on one event are not supported.')
    if definitions:
        definition = definitions[0]
        kind = definition.tag.split('}')[-1]
        node['eventDefinition'] = kind
        timers = [child for child in definition if child.tag.split('}')[-1] in
                  ('timeDuration', 'timeDate', 'timeCycle')]
        if len(timers) > 1:
            raise ValueError('A timer must have exactly one date, duration, or cycle.')
        if timers:
            timer = timers[0]
            node['timer'] = {'type': {'timeDuration': 'duration', 'timeDate': 'date',
                                    'timeCycle': 'cycle'}[timer.tag.split('}')[-1]],
                             'value': timer.text or ''}
        if kind in REFERENCE_TYPES:
            reference_kind, attribute, code = REFERENCE_TYPES[kind]
            reference_id = definition.get(attribute)
            if reference_id:
                referenced = next((child for child in root if child.get('id') == reference_id
                                   and child.tag.split('}')[-1] == reference_kind), None)
                if referenced is None:
                    raise ValueError(f'Missing event reference: {reference_id}')
                reference = {'id': reference_id}
                if referenced.get('name') is not None:
                    reference['name'] = referenced.get('name')
                if code and referenced.get(code) is not None:
                    reference['code'] = referenced.get(code)
                node['event_reference'] = reference
        if kind == 'conditionalEventDefinition':
            condition = definition.find('{*}condition')
            node['condition'] = condition.text if condition is not None else None
        if kind == 'linkEventDefinition':
            node['link_name'] = definition.get('name')
        if kind == 'compensateEventDefinition':
            if definition.get('activityRef') is not None:
                node['activity_ref'] = definition.get('activityRef')
            if definition.get('waitForCompletion') is not None:
                node['wait_for_completion'] = definition.get('waitForCompletion') in ('true', '1')
    for child in element:
        kind = child.tag.split('}')[-1]
        if kind not in ('standardLoopCharacteristics', 'multiInstanceLoopCharacteristics'):
            continue
        if 'loop' in node:
            raise ValueError('A task can have only one loop marker.')
        if kind == 'standardLoopCharacteristics':
            loop = {'type': 'standard'}
            if child.get('testBefore') is not None:
                loop['test_before'] = child.get('testBefore') in ('true', '1')
            if child.get('loopMaximum') is not None:
                loop['maximum'] = int(child.get('loopMaximum'))
            fields = {'loopCondition': 'condition'}
        else:
            loop = {'type': 'sequential' if child.get('isSequential') in ('true', '1') else 'parallel'}
            fields = {'loopCardinality': 'cardinality', 'completionCondition': 'completion_condition'}
        for expression in child:
            tag = expression.tag.split('}')[-1]
            if tag not in fields:
                raise ValueError(f'Unsupported loop configuration: {tag}')
            loop[fields[tag]] = expression.text or ''
        node['loop'] = loop
