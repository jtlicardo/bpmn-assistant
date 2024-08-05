import xml.etree.ElementTree as ET
from typing import Any


class BpmnJsonGenerator:
    """
    Class to generate the JSON representation of a BPMN process from the BPMN XML.
    """

    def __init__(self):
        self.elements = {}
        self.flows = {}

    def create_bpmn_json(self, bpmn_xml: str) -> list[dict[str, Any]]:
        """
        Create the JSON representation of the process from the BPMN XML
        """
        root = ET.fromstring(bpmn_xml)
        process_element = None

        # Find the process element
        for elem in root.iter():
            if elem.tag.endswith("process"):
                process_element = elem
                break

        if process_element is None:
            raise ValueError("No process element found in the BPMN XML")

        self._get_elements_and_flows(process_element)

        print()
        print(self.elements)
        print(self.flows)

        process = []

        for elem in process_element:

            tag = elem.tag.split("}")[-1]  # Remove namespace
            element_data = {"id": elem.get("id")}

            if tag == "startEvent":
                element_data["type"] = "startEvent"
            elif tag == "task":
                element_data["type"] = "task"
                element_data["label"] = elem.get("name")
            elif tag == "endEvent":
                element_data["type"] = "endEvent"
            else:
                continue  # Skip other elements like sequenceFlow

            process.append(element_data)

        return process

    def _get_elements_and_flows(self, process: ET.Element):
        for elem in process:
            tag = elem.tag.split("}")[-1]  # Remove namespace
            elem_id = elem.get("id")

            if tag in ["startEvent", "task", "endEvent"]:
                self.elements[elem_id] = {
                    "type": tag,
                    "id": elem_id,
                }
                if tag == "task":
                    self.elements[elem_id]["label"] = elem.get("name")
            elif tag == "sequenceFlow":
                self.flows[elem_id] = {
                    "source": elem.get("sourceRef"),
                    "target": elem.get("targetRef"),
                }
