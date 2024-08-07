import xml.etree.ElementTree as ET
from collections import deque
from typing import Any, Optional

from bpmn_assistant.core.enums import BPMNElementType


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
            - Parallel gateways must have a corresponding join gateway
            - Exclusive gateways must have a common endpoint
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
        self._build_process_structure()

        return self.process

    def _build_process_structure(self):
        start_event = next(
            elem
            for elem in self.elements.values()
            if elem["type"] == BPMNElementType.START_EVENT.value
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

        outgoing_flows = self._get_outgoing_flows(current_id)

        if current_element["type"] == BPMNElementType.EXCLUSIVE_GATEWAY.value:
            gateway = current_element.copy()
            gateway["branches"] = []
            gateway["has_join"] = False

            # Find the common endpoint of the branches
            common_endpoint = self._find_common_endpoint(current_id)
            next_after_join = None

            # If the common endpoint is an exclusive gateway, is means this gateway has a join
            if common_endpoint and self._is_exclusive_gateway(common_endpoint):
                gateway["has_join"] = True

                # Find the element after the join gateway
                join_outgoing_flows = self._get_outgoing_flows(common_endpoint)

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
            for flow in outgoing_flows:
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

        elif current_element["type"] == BPMNElementType.PARALLEL_GATEWAY.value:
            gateway = current_element.copy()
            gateway["branches"] = []

            # The join_element must be a parallel gateway with exactly one outgoing flow
            join_element = self._find_common_endpoint(current_id)

            if (
                not join_element
                or not self._is_parallel_gateway(join_element)
                or len(self._get_outgoing_flows(join_element)) != 1
            ):
                raise ValueError(
                    "Parallel gateway must have a corresponding join gateway"
                )

            # Build the branches of the parallel gateway up to the join gateway
            for flow in outgoing_flows:
                branch = self._build_structure_recursive(
                    flow["target"], stop_at=join_element
                )
                gateway["branches"].append(branch)

            result = [gateway]

            # Continue building the process from the element after the join gateway
            join_outgoing_flows = self._get_outgoing_flows(join_element)
            next_after_join = join_outgoing_flows[0]["target"]
            result.extend(self._build_structure_recursive(next_after_join, stop_at))

        elif len(outgoing_flows) == 1:
            next_id = outgoing_flows[0]["target"]
            result.extend(self._build_structure_recursive(next_id, stop_at))

        return result

    def _is_parallel_gateway(self, gateway_id: str) -> bool:
        return (
            self.elements[gateway_id]["type"] == BPMNElementType.PARALLEL_GATEWAY.value
        )

    def _is_exclusive_gateway(self, gateway_id: str) -> bool:
        return (
            self.elements[gateway_id]["type"] == BPMNElementType.EXCLUSIVE_GATEWAY.value
        )

    def _get_outgoing_flows(self, element_id: str) -> list[dict[str, str]]:
        return [flow for flow in self.flows.values() if flow["source"] == element_id]

    def _find_common_endpoint(self, gateway_id: str) -> Optional[str]:
        """
        Find the common endpoint for the branches of a gateway.
        Args:
            gateway_id: The ID of the gateway element.
        Returns:
            The ID of the common endpoint, or None if no common endpoint is found.
        """
        paths = self.trace_paths(gateway_id)

        # Go through the first path
        for element_id in paths[0]:
            # Check if element exists in every other path
            if all(element_id in path for path in paths[1:]):
                return element_id

        return None

    def trace_paths(self, gateway_id: str) -> list[list[str]]:
        """
        Trace the paths from a given gateway using BFS, constructing an ordered list of elements
        encountered along each outgoing flow.
        Args:
            gateway_id: The ID of the gateway element.
        Returns:
           A list of paths, where each path is a list of element IDs.
        """
        paths = []
        queue = deque([(gateway_id, [gateway_id])])

        while queue:
            current_id, current_path = queue.popleft()
            outgoing_flows = self._get_outgoing_flows(current_id)

            if not outgoing_flows:
                paths.append(current_path)
                continue

            for flow in outgoing_flows:
                next_id = flow["target"]
                new_path = current_path + [next_id]
                queue.append((next_id, new_path))

        # Remove the starting gateway from the paths
        paths = [path[1:] for path in paths]

        return paths

    def _get_elements_and_flows(self, process: ET.Element):
        labeled_elements = {
            BPMNElementType.TASK.value,
            BPMNElementType.USER_TASK.value,
            BPMNElementType.SERVICE_TASK.value,
            BPMNElementType.EXCLUSIVE_GATEWAY.value,
        }

        for elem in process:
            tag = elem.tag.split("}")[-1]  # Remove namespace
            elem_id = elem.get("id")

            if tag in [element.value for element in BPMNElementType]:
                self.elements[elem_id] = {
                    "type": tag,
                    "id": elem_id,
                }
                if tag in labeled_elements:
                    self.elements[elem_id]["label"] = elem.get("name")
            elif tag == "sequenceFlow":
                self.flows[elem_id] = {
                    "id": elem_id,
                    "source": elem.get("sourceRef"),
                    "target": elem.get("targetRef"),
                    "condition": elem.get("name"),
                }
