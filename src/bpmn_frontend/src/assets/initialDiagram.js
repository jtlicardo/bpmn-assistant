const initialDiagram = `<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="definitions_472e9b21-a722-4c2b-820a-004f317bc31a">
  <process id="Process_0" isExecutable="false">
  <startEvent id="start1">
    <outgoing>start1-task1</outgoing>
  </startEvent>
  <userTask id="task1" name="Describe the process">
    <incoming>start1-task1</incoming>
    <outgoing>task1-end1</outgoing>
  </userTask>
  <endEvent id="end1">
    <incoming>task1-end1</incoming>
  </endEvent>
  <sequenceFlow id="start1-task1" sourceRef="start1" targetRef="task1" />
  <sequenceFlow id="task1-end1" sourceRef="task1" targetRef="end1" />
  </process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_Process_0">
  <bpmndi:BPMNPlane id="BPMNPlane_Process_0" bpmnElement="Process_0">
    <bpmndi:BPMNShape id="start1_di" bpmnElement="start1">
      <dc:Bounds x="57" y="52" width="36" height="36" />
    </bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="task1_di" bpmnElement="task1">
      <dc:Bounds x="175" y="30" width="100" height="80" />
    </bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="end1_di" bpmnElement="end1">
      <dc:Bounds x="357" y="52" width="36" height="36" />
    </bpmndi:BPMNShape>
    <bpmndi:BPMNEdge id="start1-task1_di" bpmnElement="start1-task1">
      <di:waypoint x="93" y="70" />
      <di:waypoint x="175" y="70" />
    </bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="task1-end1_di" bpmnElement="task1-end1">
      <di:waypoint x="275" y="70" />
      <di:waypoint x="357" y="70" />
    </bpmndi:BPMNEdge>
  </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</definitions>`.trim();

export default initialDiagram;
