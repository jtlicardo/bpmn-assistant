import xml.etree.ElementTree as ET
from collections import deque
from typing import Any, Optional


class BpmnJsonGenerator:
    """
    Class to generate the JSON representation of a BPMN process from the BPMN XML.
    """

    def __init__(self):
        self.elements: dict[str, dict[str, Any]] = {}
        self.flows: dict[str, dict[str, str]] = {}
        self.process: list[dict[str, Any]] = []

    def create_bpmn_json(self, bpmn_xml: str) -> list[dict[str, Any]]:
        """
        Create the JSON representation of the process from the BPMN XML
        Constraints:
            - Supported elements: task, userTask, serviceTask, startEvent, endEvent, exclusiveGateway, parallelGateway
            - The process must have only one start event
            - The process must not contain pools or lanes
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
        # print(json.dumps(self.elements, indent=4))
        # print(json.dumps(self.flows, indent=4))

        self._build_process_structure()

        return self.process

    def _build_process_structure(self):
        start_event = next(
            elem for elem in self.elements.values() if elem["type"] == "startEvent"
        )

        # Start building the process structure recursively from the start event
        self.process = self._build_structure_recursive(start_event["id"])

    def _build_structure_recursive(
        self, current_id: str, stop_at: Optional[str] = None
    ) -> list[dict[str, Any]]:
        if current_id == stop_at:
            return []

        current_element = self.elements[current_id]
        result = [current_element]

        outgoing_flows = [
            flow for flow in self.flows.values() if flow["source"] == current_id
        ]

        if current_element["type"] == "exclusiveGateway":
            gateway = current_element.copy()
            gateway["branches"] = []
            gateway["has_join"] = False

            # Find the common endpoint of the branches
            common_endpoint = self._find_common_endpoint(current_id)
            next_after_join = None

            # If the common endpoint is an exclusive gateway, is means this gateway has a join
            if (
                common_endpoint
                and self.elements[common_endpoint]["type"] == "exclusiveGateway"
            ):
                gateway["has_join"] = True

                # Find the element after the join gateway
                join_outgoing_flows = [
                    flow
                    for flow in self.flows.values()
                    if flow["source"] == common_endpoint
                ]

                # There shouldn't be more than one outgoing flow from the join gateway
                if len(join_outgoing_flows) != 1:
                    raise ValueError(
                        "Join gateway should have exactly one outgoing flow"
                    )

                # We continue building the structure from the element after the join gateway
                next_after_join = join_outgoing_flows[0]["target"]
            else:
                # We continue building the process from the common endpoint
                next_after_join = common_endpoint

            # Build the branches of the exclusive gateway
            for i, flow in enumerate(outgoing_flows):
                branch = {
                    "condition": flow["condition"],
                    "path": self._build_structure_recursive(
                        flow["target"], stop_at=common_endpoint
                    ),
                }

                gateway["branches"].append(branch)

            result = [gateway]

            # Continue building the structure from the element after the join gateway
            if next_after_join:
                result.extend(self._build_structure_recursive(next_after_join, stop_at))

        elif current_element["type"] == "parallelGateway":
            pass

        elif len(outgoing_flows) == 1:
            next_id = outgoing_flows[0]["target"]
            result.extend(self._build_structure_recursive(next_id, stop_at))

        return result

    def _find_common_endpoint(self, gateway_id: str) -> Optional[str]:
        """
        Find the common endpoint for the branches of an exclusive gateway.
        Args:
            gateway_id: The ID of the gateway element.
        Returns:
            The ID of the common endpoint, or None if no common endpoint is found.
        """
        outgoing_flows = [
            flow for flow in self.flows.values() if flow["source"] == gateway_id
        ]
        queue = deque([flow["target"] for flow in outgoing_flows])
        visited: set[str] = set()

        while queue:
            current_id = queue.popleft()

            if current_id in visited:
                return current_id

            visited.add(current_id)

            next_flows = [
                flow for flow in self.flows.values() if flow["source"] == current_id
            ]

            for flow in next_flows:
                queue.append(flow["target"])

        return None

    def _get_elements_and_flows(self, process: ET.Element):
        for elem in process:
            tag = elem.tag.split("}")[-1]  # Remove namespace
            elem_id = elem.get("id")

            if tag in [
                "startEvent",
                "endEvent",
                "task",
                "userTask",
                "serviceTask",
                "exclusiveGateway",
                "parallelGateway",
            ]:
                self.elements[elem_id] = {
                    "type": tag,
                    "id": elem_id,
                }
                if tag in ["task", "userTask", "serviceTask", "exclusiveGateway"]:
                    self.elements[elem_id]["label"] = elem.get("name")
            elif tag == "sequenceFlow":
                self.flows[elem_id] = {
                    "id": elem_id,
                    "source": elem.get("sourceRef"),
                    "target": elem.get("targetRef"),
                    "condition": elem.get("name"),
                }
