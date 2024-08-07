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

    def _build_structure_recursive(self, current_id: str) -> list[dict[str, Any]]:
        current_element = self.elements[current_id]
        result = [current_element]

        outgoing_flows = [
            flow for flow in self.flows.values() if flow["source"] == current_id
        ]

        if current_element["type"] in ["exclusiveGateway", "parallelGateway"]:
            gateway = current_element.copy()
            gateway["branches"] = []
            gateway["has_join"] = False

            # Find the common endpoint and the paths for each branch
            common_endpoint, branch_paths = self._find_branch_endpoints(current_id)

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

                # We will continue building the structure from the target of the outgoing flow
                common_endpoint = join_outgoing_flows[0]["target"]

            for i, flow in enumerate(outgoing_flows):
                branch = {
                    "condition": flow["condition"],
                    "path": branch_paths[i],
                }
                gateway["branches"].append(branch)

            result = [gateway]

            # Continue building the structure from the common endpoint
            if common_endpoint:
                result.extend(self._build_structure_recursive(common_endpoint))

        elif len(outgoing_flows) == 1:
            next_id = outgoing_flows[0]["target"]
            result.extend(self._build_structure_recursive(next_id))

        return result

    def _find_branch_endpoints(
        self, gateway_id: str
    ) -> tuple[Optional[str], list[list[dict[str, Any]]]]:
        """
        Find the common endpoint for the branches of an exclusive gateway, handling nested gateways.
        Args:
            gateway_id: The ID of the gateway element.
        Returns:
            A tuple containing the ID of the common endpoint and the paths of the branches.
        """

        outgoing_flows = [
            flow for flow in self.flows.values() if flow["source"] == gateway_id
        ]
        queue = deque([(flow["target"], []) for flow in outgoing_flows])
        visited: set[str] = set()
        branch_paths: list[list[dict[str, Any]]] = [[] for _ in outgoing_flows]

        while queue:
            # Get the next node and its path from the queue
            current_id, path = queue.popleft()

            # If we've visited this node before, it's the common endpoint
            if current_id in visited:

                # Remove the common endpoint from all branch paths
                for i in range(len(branch_paths)):
                    if branch_paths[i] and branch_paths[i][-1]["id"] == current_id:
                        branch_paths[i] = branch_paths[i][:-1]

                return current_id, branch_paths

            # Mark the current node as visited
            visited.add(current_id)

            # Get the current element
            current_element = self.elements[current_id]

            if current_element["type"] in ["exclusiveGateway", "parallelGateway"]:
                # Recursively build the structure for nested gateways
                nested_structure = self._build_structure_recursive(current_id)
                path.extend(nested_structure)

                # Find the last element of the nested structure to continue from
                last_element = nested_structure[-1]
                if isinstance(last_element, dict) and last_element.get("type") in [
                    "exclusiveGateway",
                    "parallelGateway",
                ]:
                    # If the last element is a gateway, we need to find its endpoint
                    nested_endpoint, _ = self._find_branch_endpoints(last_element["id"])
                    if nested_endpoint:
                        current_id = nested_endpoint
                else:
                    current_id = last_element["id"]
            else:
                # If the current element is not a gateway, add it to the path
                path.append(current_element)

            # Determine which branch this path belongs to and update branch_paths
            for i, initial_flow in enumerate(outgoing_flows):
                if initial_flow["target"] == path[0]["id"]:
                    branch_paths[i] = path[:]
                    break

            # Get all outgoing flows from the current node
            next_flows = [
                flow for flow in self.flows.values() if flow["source"] == current_id
            ]

            # Add the targets of these flows to the queue
            for flow in next_flows:
                queue.append((flow["target"], path[:]))

        # If we've exhausted the queue without finding a common endpoint,
        # return None as the endpoint and the paths we've found
        return None, branch_paths

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
