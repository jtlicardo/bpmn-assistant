from bpmn_assistant.services import BpmnXmlGenerator
from xml.dom import minidom


def pretty_print_xml(xml_string: str) -> str:
    return minidom.parseString(xml_string).toprettyxml()


class TestBpmnXmlGenerator:
    def test_create_bpmn_xml_1(self, procurement_process_fixture):

        bpmn_xml_generator = BpmnXmlGenerator()

        result = bpmn_xml_generator.create_bpmn_xml(procurement_process_fixture)

        expected_xml = '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="definitions_1"><process id="Process_1" isExecutable="false"><startEvent id="start1"><outgoing>start1-parallel1</outgoing></startEvent><parallelGateway id="parallel1"><incoming>start1-parallel1</incoming><outgoing>parallel1-task1</outgoing><outgoing>parallel1-task3</outgoing></parallelGateway><task id="task1" name="Send mail to supplier"><incoming>parallel1-task1</incoming><outgoing>task1-task2</outgoing></task><task id="task2" name="Prepare the documents"><incoming>task1-task2</incoming><outgoing>task2-join1</outgoing></task><task id="task3" name="Search for the goods"><incoming>parallel1-task3</incoming><outgoing>task3-task4</outgoing></task><task id="task4" name="Pick up the goods"><incoming>task3-task4</incoming><outgoing>task4-join1</outgoing></task><parallelGateway id="join1"><incoming>task2-join1</incoming><incoming>task4-join1</incoming><outgoing>join1-end1</outgoing></parallelGateway><endEvent id="end1"><incoming>join1-end1</incoming></endEvent><sequenceFlow id="start1-parallel1" sourceRef="start1" targetRef="parallel1" /><sequenceFlow id="task1-task2" sourceRef="task1" targetRef="task2" /><sequenceFlow id="task2-join1" sourceRef="task2" targetRef="join1" /><sequenceFlow id="parallel1-task1" sourceRef="parallel1" targetRef="task1" /><sequenceFlow id="task3-task4" sourceRef="task3" targetRef="task4" /><sequenceFlow id="task4-join1" sourceRef="task4" targetRef="join1" /><sequenceFlow id="parallel1-task3" sourceRef="parallel1" targetRef="task3" /><sequenceFlow id="join1-end1" sourceRef="join1" targetRef="end1" /></process></definitions>'

        assert result == expected_xml

    def test_create_bpmn_xml_2(self, order_process_fixture):
        bpmn_xml_generator = BpmnXmlGenerator()

        result = bpmn_xml_generator.create_bpmn_xml(order_process_fixture)

        expected_xml = '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="definitions_1"><process id="Process_1" isExecutable="false"><startEvent id="start1"><outgoing>start1-task1</outgoing></startEvent><task id="task1" name="Receive order from customer"><incoming>start1-task1</incoming><outgoing>task1-exclusive1</outgoing></task><exclusiveGateway id="exclusive1" name="Product in stock?"><incoming>task1-exclusive1</incoming><outgoing>exclusive1-task2</outgoing><outgoing>exclusive1-exclusive2</outgoing></exclusiveGateway><task id="task2" name="Notify customer that order cannot be fulfilled"><incoming>exclusive1-task2</incoming><outgoing>task2-end1</outgoing></task><exclusiveGateway id="exclusive2" name="Payment succeeds?"><incoming>exclusive1-exclusive2</incoming><outgoing>exclusive2-task3</outgoing><outgoing>exclusive2-task5</outgoing></exclusiveGateway><task id="task3" name="Process order"><incoming>exclusive2-task3</incoming><outgoing>task3-task4</outgoing></task><task id="task4" name="Notify customer that order has been processed"><incoming>task3-task4</incoming><outgoing>task4-end1</outgoing></task><task id="task5" name="Notify customer that order cannot be processed"><incoming>exclusive2-task5</incoming><outgoing>task5-end1</outgoing></task><endEvent id="end1"><incoming>task2-end1</incoming><incoming>task4-end1</incoming><incoming>task5-end1</incoming></endEvent><sequenceFlow id="start1-task1" sourceRef="start1" targetRef="task1" /><sequenceFlow id="task1-exclusive1" sourceRef="task1" targetRef="exclusive1" /><sequenceFlow id="task2-end1" sourceRef="task2" targetRef="end1" /><sequenceFlow id="exclusive1-task2" sourceRef="exclusive1" targetRef="task2" name="Product is out of stock" /><sequenceFlow id="task3-task4" sourceRef="task3" targetRef="task4" /><sequenceFlow id="task4-end1" sourceRef="task4" targetRef="end1" /><sequenceFlow id="exclusive2-task3" sourceRef="exclusive2" targetRef="task3" name="Payment succeeds" /><sequenceFlow id="task5-end1" sourceRef="task5" targetRef="end1" /><sequenceFlow id="exclusive2-task5" sourceRef="exclusive2" targetRef="task5" name="Payment fails" /><sequenceFlow id="exclusive1-exclusive2" sourceRef="exclusive1" targetRef="exclusive2" name="Product is in stock" /></process></definitions>'

        assert result == expected_xml

    def test_create_bpmn_xml_3(self, linear_process_fixture):
        bpmn_xml_generator = BpmnXmlGenerator()

        result = bpmn_xml_generator.create_bpmn_xml(linear_process_fixture)

        expected_xml = '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="definitions_1"><process id="Process_1" isExecutable="false"><startEvent id="start1"><outgoing>start1-task1</outgoing></startEvent><task id="task1" name="Receive customer inquiry"><incoming>start1-task1</incoming><outgoing>task1-task2</outgoing></task><userTask id="task2" name="Review product catalog"><incoming>task1-task2</incoming><outgoing>task2-task3</outgoing></userTask><task id="task3" name="Prepare quote"><incoming>task2-task3</incoming><outgoing>task3-task4</outgoing></task><serviceTask id="task4" name="Send quote to customer"><incoming>task3-task4</incoming><outgoing>task4-task5</outgoing></serviceTask><task id="task5" name="Follow up with customer"><incoming>task4-task5</incoming><outgoing>task5-end1</outgoing></task><endEvent id="end1"><incoming>task5-end1</incoming></endEvent><sequenceFlow id="start1-task1" sourceRef="start1" targetRef="task1" /><sequenceFlow id="task1-task2" sourceRef="task1" targetRef="task2" /><sequenceFlow id="task2-task3" sourceRef="task2" targetRef="task3" /><sequenceFlow id="task3-task4" sourceRef="task3" targetRef="task4" /><sequenceFlow id="task4-task5" sourceRef="task4" targetRef="task5" /><sequenceFlow id="task5-end1" sourceRef="task5" targetRef="end1" /></process></definitions>'

        assert result == expected_xml
