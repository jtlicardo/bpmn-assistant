const { layoutProcess } = require('bpmn-auto-layout');

let bpmnXml = `
<?xml version="1.0" ?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="definitions_4f3fb223-1419-4b21-839d-95e5f8bffd73">
	<process id="Process_0" isExecutable="false">
		<startEvent id="start1">
			<outgoing>start1-task1</outgoing>
		</startEvent>
		<userTask id="task1" name="Log in to the university's website">
			<incoming>start1-task1</incoming>
			<outgoing>task1-task2</outgoing>
		</userTask>
		<userTask id="task2" name="Take an online exam">
			<incoming>task1-task2</incoming>
			<incoming>task4-task2</incoming>
			<outgoing>task2-task3</outgoing>
		</userTask>
		<serviceTask id="task3" name="Grade the exam">
			<incoming>task2-task3</incoming>
			<outgoing>task3-exclusive1</outgoing>
		</serviceTask>
		<exclusiveGateway id="exclusive1" name="Score below 60%?">
			<incoming>task3-exclusive1</incoming>
			<outgoing>exclusive1-task4</outgoing>
			<outgoing>exclusive1-task5</outgoing>
		</exclusiveGateway>
		<userTask id="task4" name="Take the exam again">
			<incoming>exclusive1-task4</incoming>
			<outgoing>task4-task2</outgoing>
		</userTask>
		<userTask id="task5" name="Professor enters the grade">
			<incoming>exclusive1-task5</incoming>
			<outgoing>task5-end1</outgoing>
		</userTask>
		<endEvent id="end1">
			<incoming>task5-end1</incoming>
		</endEvent>
		<sequenceFlow id="start1-task1" sourceRef="start1" targetRef="task1"/>
		<sequenceFlow id="task1-task2" sourceRef="task1" targetRef="task2"/>
		<sequenceFlow id="task2-task3" sourceRef="task2" targetRef="task3"/>
		<sequenceFlow id="task3-exclusive1" sourceRef="task3" targetRef="exclusive1"/>
		<sequenceFlow id="exclusive1-task4" sourceRef="exclusive1" targetRef="task4" name="Score below 60%"/>
		<sequenceFlow id="exclusive1-task5" sourceRef="exclusive1" targetRef="task5" name="Score 60% or higher"/>
		<sequenceFlow id="task4-task2" sourceRef="task4" targetRef="task2"/>
		<sequenceFlow id="task5-end1" sourceRef="task5" targetRef="end1"/>
	</process>
</definitions>
`;

async function layoutBpmnXml(bpmnXml) {
    try {
        return await layoutProcess(bpmnXml);
    } catch (error) {
        console.error('Error processing BPMN XML:', error);
        return null;
    }
}

// Example usage
layoutBpmnXml(bpmnXml).then((layoutedXml) => {
    console.log(layoutedXml);
});

