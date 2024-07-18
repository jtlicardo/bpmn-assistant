from xml.etree import ElementTree

from bpmn_assistant.config import logger


def validate_bpmn(xml_content: str) -> bool:
    """
    Validate the BPMN XML content based on the supported elements.
    Args:
        xml_content: The BPMN XML content.
    Returns:
        bool: True if the BPMN XML is valid, False otherwise.
    """
    supported_elements = {
        "definitions",
        "process",
        "incoming",
        "outgoing",
        "task",
        "userTask",
        "serviceTask",
        "exclusiveGateway",
        "parallelGateway",
        "startEvent",
        "endEvent",
        "sequenceFlow",
    }

    try:
        tree = ElementTree.fromstring(xml_content)
        # Namespace map to handle XML namespaces in the tags
        namespaces = {
            "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
            "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
            "dc": "http://www.omg.org/spec/DD/20100524/DC",
            "di": "http://www.omg.org/spec/DD/20100524/DI",
        }

        # Iterate over all elements in the XML and check their tags
        for elem in tree.iter():
            # Strip the namespace if it exists
            tag = elem.tag.split("}")[-1]
            # Check if the tag is a supported element
            if tag not in supported_elements and not tag.startswith(
                ("BPMN", "Bounds", "waypoint")
            ):
                logger.info(f"Unsupported element: {tag}")
                return False
        return True
    except ElementTree.ParseError as e:
        logger.error(f"Error parsing the BPMN XML: {str(e)}", exc_info=e)
        return False


if __name__ == "__main__":
    xml_data = """<?xml version="1.0" encoding="UTF-8"?><definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="definitions_51812ef7-e532-4554-8584-8142d04d8410"><process id="Process_0" isExecutable="false"><startEvent id="start1"><outgoing>start1-parallel1</outgoing></startEvent><userTask id="task1" name="Send mail to supplier"><incoming>parallel1-task1</incoming><outgoing>task1-task2</outgoing></userTask><userTask id="task2" name="Prepare documents"><incoming>task1-task2</incoming><outgoing>task2-parallel2</outgoing></userTask><userTask id="task3" name="Search for goods"><incoming>parallel1-task3</incoming><outgoing>task3-task4</outgoing></userTask><userTask id="task4" name="Pick up goods"><incoming>task3-task4</incoming><outgoing>task4-parallel2</outgoing></userTask><parallelGateway id="parallel1"><incoming>start1-parallel1</incoming><outgoing>parallel1-task1</outgoing><outgoing>parallel1-task3</outgoing></parallelGateway><parallelGateway id="parallel2"><incoming>task2-parallel2</incoming><incoming>task4-parallel2</incoming><outgoing>parallel2-end1</outgoing></parallelGateway><endEvent id="end1"><incoming>parallel2-end1</incoming></endEvent><sequenceFlow id="start1-parallel1" sourceRef="start1" targetRef="parallel1" /><sequenceFlow id="parallel1-task1" sourceRef="parallel1" targetRef="task1" /><sequenceFlow id="parallel1-task3" sourceRef="parallel1" targetRef="task3" /><sequenceFlow id="task1-task2" sourceRef="task1" targetRef="task2" /><sequenceFlow id="task3-task4" sourceRef="task3" targetRef="task4" /><sequenceFlow id="task2-parallel2" sourceRef="task2" targetRef="parallel2" /><sequenceFlow id="task4-parallel2" sourceRef="task4" targetRef="parallel2" /><sequenceFlow id="parallel2-end1" sourceRef="parallel2" targetRef="end1" /></process><bpmndi:BPMNDiagram id="BPMNDiagram_Process_0"><bpmndi:BPMNPlane id="BPMNPlane_Process_0" bpmnElement="Process_0"><bpmndi:BPMNShape id="start1_di" bpmnElement="start1"><dc:Bounds x="57" y="52" width="36" height="36" /></bpmndi:BPMNShape><bpmndi:BPMNShape id="task1_di" bpmnElement="task1"><dc:Bounds x="325" y="30" width="100" height="80" /></bpmndi:BPMNShape><bpmndi:BPMNShape id="task2_di" bpmnElement="task2"><dc:Bounds x="475" y="30" width="100" height="80" /></bpmndi:BPMNShape><bpmndi:BPMNShape id="task3_di" bpmnElement="task3"><dc:Bounds x="325" y="170" width="100" height="80" /></bpmndi:BPMNShape><bpmndi:BPMNShape id="task4_di" bpmnElement="task4"><dc:Bounds x="475" y="170" width="100" height="80" /></bpmndi:BPMNShape><bpmndi:BPMNShape id="parallel1_di" bpmnElement="parallel1"><dc:Bounds x="200" y="45" width="50" height="50" /></bpmndi:BPMNShape><bpmndi:BPMNShape id="parallel2_di" bpmnElement="parallel2"><dc:Bounds x="650" y="45" width="50" height="50" /></bpmndi:BPMNShape><bpmndi:BPMNShape id="end1_di" bpmnElement="end1"><dc:Bounds x="807" y="52" width="36" height="36" /></bpmndi:BPMNShape><bpmndi:BPMNEdge id="start1-parallel1_di" bpmnElement="start1-parallel1"><di:waypoint x="93" y="70" /><di:waypoint x="200" y="70" /></bpmndi:BPMNEdge><bpmndi:BPMNEdge id="parallel1-task1_di" bpmnElement="parallel1-task1"><di:waypoint x="250" y="70" /><di:waypoint x="325" y="70" /></bpmndi:BPMNEdge><bpmndi:BPMNEdge id="parallel1-task3_di" bpmnElement="parallel1-task3"><di:waypoint x="225" y="95" /><di:waypoint x="225" y="210" /><di:waypoint x="325" y="210" /></bpmndi:BPMNEdge><bpmndi:BPMNEdge id="task1-task2_di" bpmnElement="task1-task2"><di:waypoint x="425" y="70" /><di:waypoint x="475" y="70" /></bpmndi:BPMNEdge><bpmndi:BPMNEdge id="task3-task4_di" bpmnElement="task3-task4"><di:waypoint x="425" y="210" /><di:waypoint x="475" y="210" /></bpmndi:BPMNEdge><bpmndi:BPMNEdge id="task2-parallel2_di" bpmnElement="task2-parallel2"><di:waypoint x="575" y="70" /><di:waypoint x="650" y="70" /></bpmndi:BPMNEdge><bpmndi:BPMNEdge id="task4-parallel2_di" bpmnElement="task4-parallel2"><di:waypoint x="575" y="210" /><di:waypoint x="675" y="210" /><di:waypoint x="675" y="95" /></bpmndi:BPMNEdge><bpmndi:BPMNEdge id="parallel2-end1_di" bpmnElement="parallel2-end1"><di:waypoint x="700" y="70" /><di:waypoint x="807" y="70" /></bpmndi:BPMNEdge></bpmndi:BPMNPlane></bpmndi:BPMNDiagram></definitions>"""
    print(validate_bpmn(xml_data))

    send_task = """<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_03evaz1" targetNamespace="http://bpmn.io/schema/bpmn" exporter="bpmn-js (https://demo.bpmn.io)" exporterVersion="17.2.1"><bpmn:process id="Process_1i5mjtw" isExecutable="false"><bpmn:startEvent id="StartEvent_1su8l78"><bpmn:outgoing>Flow_1u0u5t6</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow id="Flow_1u0u5t6" sourceRef="StartEvent_1su8l78" targetRef="Activity_13obw0t" /><bpmn:sendTask id="Activity_13obw0t"><bpmn:incoming>Flow_1u0u5t6</bpmn:incoming><bpmn:outgoing>Flow_0rv8me8</bpmn:outgoing></bpmn:sendTask><bpmn:endEvent id="Event_0ce5c5e"><bpmn:incoming>Flow_0rv8me8</bpmn:incoming></bpmn:endEvent><bpmn:sequenceFlow id="Flow_0rv8me8" sourceRef="Activity_13obw0t" targetRef="Event_0ce5c5e" /></bpmn:process><bpmndi:BPMNDiagram id="BPMNDiagram_1"><bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1i5mjtw"><bpmndi:BPMNShape id="_BPMNShape_StartEvent_2" bpmnElement="StartEvent_1su8l78"><dc:Bounds x="156" y="82" width="36" height="36" /></bpmndi:BPMNShape><bpmndi:BPMNShape id="Activity_0cuj62p_di" bpmnElement="Activity_13obw0t"><dc:Bounds x="260" y="60" width="100" height="80" /></bpmndi:BPMNShape><bpmndi:BPMNShape id="Event_0ce5c5e_di" bpmnElement="Event_0ce5c5e"><dc:Bounds x="432" y="82" width="36" height="36" /></bpmndi:BPMNShape><bpmndi:BPMNEdge id="Flow_1u0u5t6_di" bpmnElement="Flow_1u0u5t6"><di:waypoint x="192" y="100" /><di:waypoint x="260" y="100" /></bpmndi:BPMNEdge><bpmndi:BPMNEdge id="Flow_0rv8me8_di" bpmnElement="Flow_0rv8me8"><di:waypoint x="360" y="100" /><di:waypoint x="432" y="100" /></bpmndi:BPMNEdge></bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>"""
    print(validate_bpmn(send_task))

    intermediate = """<?xml version="1.0" encoding="UTF-8"?><bpmn:definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_0eke3l8" targetNamespace="http://bpmn.io/schema/bpmn" exporter="bpmn-js (https://demo.bpmn.io)" exporterVersion="17.2.1"><bpmn:process id="Process_06swux1" isExecutable="false"><bpmn:startEvent id="StartEvent_0eyr0q9"><bpmn:outgoing>Flow_1vassn7</bpmn:outgoing></bpmn:startEvent><bpmn:intermediateThrowEvent id="Event_0lzz65l"><bpmn:incoming>Flow_1vassn7</bpmn:incoming><bpmn:outgoing>Flow_0rn6lr2</bpmn:outgoing></bpmn:intermediateThrowEvent><bpmn:sequenceFlow id="Flow_1vassn7" sourceRef="StartEvent_0eyr0q9" targetRef="Event_0lzz65l" /><bpmn:endEvent id="Event_16uswyt"><bpmn:incoming>Flow_0rn6lr2</bpmn:incoming></bpmn:endEvent><bpmn:sequenceFlow id="Flow_0rn6lr2" sourceRef="Event_0lzz65l" targetRef="Event_16uswyt" /></bpmn:process><bpmndi:BPMNDiagram id="BPMNDiagram_1"><bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_06swux1"><bpmndi:BPMNShape id="_BPMNShape_StartEvent_2" bpmnElement="StartEvent_0eyr0q9"><dc:Bounds x="156" y="82" width="36" height="36" /></bpmndi:BPMNShape><bpmndi:BPMNShape id="Event_0lzz65l_di" bpmnElement="Event_0lzz65l"><dc:Bounds x="242" y="82" width="36" height="36" /></bpmndi:BPMNShape><bpmndi:BPMNShape id="Event_16uswyt_di" bpmnElement="Event_16uswyt"><dc:Bounds x="332" y="82" width="36" height="36" /></bpmndi:BPMNShape><bpmndi:BPMNEdge id="Flow_1vassn7_di" bpmnElement="Flow_1vassn7"><di:waypoint x="192" y="100" /><di:waypoint x="242" y="100" /></bpmndi:BPMNEdge><bpmndi:BPMNEdge id="Flow_0rn6lr2_di" bpmnElement="Flow_0rn6lr2"><di:waypoint x="278" y="100" /><di:waypoint x="332" y="100" /></bpmndi:BPMNEdge></bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>"""
    print(validate_bpmn(intermediate))
