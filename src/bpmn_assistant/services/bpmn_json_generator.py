import xml.etree.ElementTree as ET
from collections import deque
from typing import Any, Callable, Optional

from bpmn_assistant.core.enums import BPMNElementType


class BpmnJsonGenerator:
    """
    Class to generate the JSON representation of a BPMN process from the BPMN XML.
    """

    def __init__(self):
        self.elements: dict[str, dict[str, Any]] = {}
        self.flows: dict[str, dict[str, Any]] = {}
        self.process: list[dict[str, Any]] = []

    def _find_process_element(self, root: ET.Element) -> ET.Element:
        for elem in root.iter():
            if elem.tag.endswith("process"):
                return elem
        raise ValueError("No process element found in the BPMN XML")

    def _get_outgoing_flows(self, element_id: str) -> list[dict[str, str]]:
        return [flow for flow in self.flows.values() if flow["source"] == element_id]

    def _build_structure_recursive(
        self,
        current_id: str,
        stop_at: Optional[str] = None,
        visited: Optional[set] = None,
    ) -> list[dict[str, Any]]:
        if visited is None:
            visited = set()

        if current_id in visited or current_id == stop_at:
            return []

        visited.add(current_id)

        current_element = self.elements[current_id]

        handler = self._get_gateway_handler(current_element["type"])
        if handler:
            return handler(current_id, stop_at, visited)

        result = [current_element]
        outgoing_flows = self._get_outgoing_flows(current_id)

        if len(outgoing_flows) == 1:
            next_id = outgoing_flows[0]["target"]
            result.extend(self._build_structure_recursive(next_id, stop_at, visited))

        return result

    def _build_process_structure(self):
        start_event = next(
            elem
            for elem in self.elements.values()
            if elem["type"] == BPMNElementType.START_EVENT.value
        )

        # Start building the process structure recursively from the start event
        self.process = self._build_structure_recursive(start_event["id"])

    def _get_elements_and_flows(self, process: ET.Element):
        labeled_elements = {
            BPMNElementType.TASK.value,
            BPMNElementType.USER_TASK.value,
            BPMNElementType.SERVICE_TASK.value,
            BPMNElementType.SEND_TASK.value,
            BPMNElementType.RECEIVE_TASK.value,
            BPMNElementType.BUSINESS_RULE_TASK.value,
            BPMNElementType.MANUAL_TASK.value,
            BPMNElementType.SCRIPT_TASK.value,
            BPMNElementType.EXCLUSIVE_GATEWAY.value,
            BPMNElementType.INCLUSIVE_GATEWAY.value,
            BPMNElementType.START_EVENT.value,
            BPMNElementType.END_EVENT.value,
            BPMNElementType.INTERMEDIATE_THROW_EVENT.value,
            BPMNElementType.INTERMEDIATE_CATCH_EVENT.value,
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
                    name = elem.get("name")
                    if name:  # Only add label if name exists and is not empty
                        self.elements[elem_id]["label"] = name

                # Store default flow for inclusive/exclusive gateways
                if tag in [BPMNElementType.INCLUSIVE_GATEWAY.value, BPMNElementType.EXCLUSIVE_GATEWAY.value]:
                    default_flow = elem.get("default")
                    if default_flow:
                        self.elements[elem_id]["default_flow"] = default_flow

                # Check for event definitions (timerEventDefinition, messageEventDefinition, etc.)
                for child in elem:
                    child_tag = child.tag.split("}")[-1]
                    if child_tag.endswith("EventDefinition"):
                        self.elements[elem_id]["eventDefinition"] = child_tag
                        break
            elif tag == "sequenceFlow":
                self.flows[elem_id] = {
                    "id": elem_id,
                    "source": elem.get("sourceRef"),
                    "target": elem.get("targetRef"),
                    "condition": elem.get("name"),
                }

    def create_bpmn_json(self, bpmn_xml: str) -> list[dict[str, Any]]:
        """
        Create the JSON representation of the process from the BPMN XML
        Constraints:
            - Supported elements: task, userTask, serviceTask, sendTask, receiveTask, businessRuleTask, manualTask, scriptTask, startEvent, endEvent, intermediateThrowEvent, intermediateCatchEvent, exclusiveGateway, inclusiveGateway, parallelGateway
            - Supported event definitions: timerEventDefinition, messageEventDefinition
            - The process must have only one start event
            - The process must not contain pools or lanes
            - Parallel gateways must have a corresponding join gateway
        """
        root = ET.fromstring(bpmn_xml)
        process_element = self._find_process_element(root)
        self._get_elements_and_flows(process_element)
        start_events = [
            elem
            for elem in self.elements.values()
            if elem["type"] == BPMNElementType.START_EVENT.value
        ]
        if len(start_events) != 1:
            raise ValueError("Process must contain exactly one start event")
        self._build_process_structure()
        return self.process

    def _trace_paths(self, gateway_id: str) -> list[list[str]]:
        """
        Trace the paths from a given gateway using BFS, constructing an ordered list of elements
        encountered along each outgoing flow. Handles loops by stopping when an element is revisited.
        Args:
            gateway_id: The ID of the gateway element.
        Returns:
           A list of paths, where each path is a list of element IDs.
        """
        paths = []

        # The queue contains the current element, the path taken so far, and the visited elements
        queue = deque([(gateway_id, [gateway_id], {gateway_id})])

        while queue:
            current_id, current_path, visited = queue.popleft()
            outgoing_flows = self._get_outgoing_flows(current_id)

            if not outgoing_flows:
                paths.append(current_path)
                continue

            for flow in outgoing_flows:
                next_id = flow["target"]
                if next_id not in visited:
                    new_path = current_path + [next_id]
                    new_visited = visited.copy()
                    new_visited.add(next_id)
                    queue.append((next_id, new_path, new_visited))
                else:
                    # We've encountered a loop, add this path to the results
                    paths.append(current_path + [next_id])

        # Remove the starting gateway from the paths
        paths = [path[1:] for path in paths]

        return paths

    def _find_common_branch_endpoint(self, gateway_id: str) -> Optional[str]:
        """
        Find the common endpoint for the branches of a gateway.
        Args:
            gateway_id: The ID of the gateway element.
        Returns:
            The ID of the common endpoint, or None if no common endpoint is found.
        """
        paths = self._trace_paths(gateway_id)

        for element_id in paths[0]:
            if all(element_id in path for path in paths[1:]):
                return element_id

        return None

    def _populate_branch_transitions(
        self,
        *,
        branch: dict[str, Any],
        branch_path: list[dict[str, Any]],
        flow: dict[str, str],
        common_branch_endpoint: Optional[str],
    ) -> None:
        """Populate `next` pointers for a branch, recursing into nested gateways as needed."""
        if not branch_path:
            if flow["target"] != common_branch_endpoint:
                branch["next"] = flow["target"]
            return

        last_element = branch_path[-1]
        last_outgoing_flows = self._get_outgoing_flows(last_element["id"])

        if last_element["type"] in {
            BPMNElementType.INCLUSIVE_GATEWAY.value,
            BPMNElementType.EXCLUSIVE_GATEWAY.value,
        }:
            self._handle_nested_gateway_branch(
                branch=branch,
                last_element=last_element,
                last_outgoing_flows=last_outgoing_flows,
                common_branch_endpoint=common_branch_endpoint,
            )
        elif last_element["type"] == BPMNElementType.PARALLEL_GATEWAY.value:
            join_id = self._find_common_branch_endpoint(last_element["id"])
            if join_id is None:
                raise ValueError("Parallel gateway should have a corresponding join gateway")
            join_outgoing_flows = self._get_outgoing_flows(join_id)
            if len(join_outgoing_flows) != 1:
                raise ValueError("Join gateway should have one outgoing flow")
            join_target = join_outgoing_flows[0]["target"]
            if join_target != common_branch_endpoint:
                branch["next"] = join_target
        elif (
            len(last_outgoing_flows) == 1
            and last_outgoing_flows[0]["target"] != common_branch_endpoint
        ):
            branch["next"] = last_outgoing_flows[0]["target"]

    def _build_eg_branch(
        self,
        branch_path: list[dict[str, Any]],
        common_branch_endpoint: Optional[str],
        flow: dict[str, str],
    ) -> dict[str, Any]:
        """
        Build the branch structure for an exclusive gateway.
        Args:
            branch_path: The structure of the branch.
            common_branch_endpoint: The ID of the common endpoint for the branches of the gateway.
            flow: The flow object of the branch.
        Returns:
            The branch structure ("condition", "path", "next").
        """
        branch = {
            "condition": flow["condition"],
            "path": branch_path,
        }

        self._populate_branch_transitions(
            branch=branch,
            branch_path=branch_path,
            flow=flow,
            common_branch_endpoint=common_branch_endpoint,
        )

        return branch

    def _is_exclusive_gateway(self, gateway_id: str) -> bool:
        return (
            self.elements[gateway_id]["type"] == BPMNElementType.EXCLUSIVE_GATEWAY.value
        )

    def _build_exclusive_gateway(
        self,
        gateway_id: str,
        stop_at: Optional[str],
        visited: set[str],
    ) -> list[dict[str, Any]]:
        """Build the structure produced when traversing an exclusive gateway and its branches."""
        gateway = self.elements[gateway_id].copy()
        gateway["branches"] = []
        gateway["has_join"] = False

        outgoing_flows = self._get_outgoing_flows(gateway_id)
        common_branch_endpoint = self._find_common_branch_endpoint(gateway_id)
        next_element = None

        if common_branch_endpoint and self._is_exclusive_gateway(common_branch_endpoint):
            gateway["has_join"] = True
            join_outgoing_flows = self._get_outgoing_flows(common_branch_endpoint)
            if len(join_outgoing_flows) != 1:
                raise ValueError("Join gateway should have exactly one outgoing flow")
            next_element = join_outgoing_flows[0]["target"]
        else:
            next_element = common_branch_endpoint

        for flow in outgoing_flows:
            branch_path = self._build_structure_recursive(
                flow["target"],
                stop_at=common_branch_endpoint,
                visited=visited,
            )
            branch = self._build_eg_branch(branch_path, common_branch_endpoint, flow)
            gateway["branches"].append(branch)

        result = [gateway]
        if next_element:
            result.extend(
                self._build_structure_recursive(next_element, stop_at, visited)
            )
        return result

    def _build_ig_branch(
        self,
        branch_path: list[dict[str, Any]],
        common_branch_endpoint: Optional[str],
        flow: dict[str, str],
        default_flow_id: Optional[str],
    ) -> dict[str, Any]:
        """
        Build the branch structure for an inclusive gateway.
        Args:
            branch_path: The structure of the branch.
            common_branch_endpoint: The ID of the common endpoint for the branches of the gateway.
            flow: The flow object of the branch.
            default_flow_id: The ID of the default flow (if any).
        Returns:
            The branch structure ("condition", "path", "next", "is_default").
        """
        is_default = flow["id"] == default_flow_id

        branch = {
            "path": branch_path,
            "is_default": is_default,
        }

        # Only add condition if not default
        if not is_default:
            branch["condition"] = flow["condition"]

        self._populate_branch_transitions(
            branch=branch,
            branch_path=branch_path,
            flow=flow,
            common_branch_endpoint=common_branch_endpoint,
        )

        return branch

    def _is_inclusive_gateway(self, gateway_id: str) -> bool:
        return (
            self.elements[gateway_id]["type"] == BPMNElementType.INCLUSIVE_GATEWAY.value
        )

    def _build_inclusive_gateway(
        self,
        gateway_id: str,
        stop_at: Optional[str],
        visited: set[str],
    ) -> list[dict[str, Any]]:
        """Build the structure produced when traversing an inclusive gateway and its branches."""
        gateway = self.elements[gateway_id].copy()
        gateway["branches"] = []
        gateway["has_join"] = False

        outgoing_flows = self._get_outgoing_flows(gateway_id)
        common_branch_endpoint = self._find_common_branch_endpoint(gateway_id)
        next_element = None

        if common_branch_endpoint and self._is_inclusive_gateway(common_branch_endpoint):
            gateway["has_join"] = True
            join_outgoing_flows = self._get_outgoing_flows(common_branch_endpoint)
            if len(join_outgoing_flows) != 1:
                raise ValueError("Join gateway should have exactly one outgoing flow")
            next_element = join_outgoing_flows[0]["target"]
        else:
            next_element = common_branch_endpoint

        default_flow_id = gateway.get("default_flow")

        for flow in outgoing_flows:
            branch_path = self._build_structure_recursive(
                flow["target"],
                stop_at=common_branch_endpoint,
                visited=visited,
            )
            branch = self._build_ig_branch(
                branch_path, common_branch_endpoint, flow, default_flow_id
            )
            gateway["branches"].append(branch)

        gateway.pop("default_flow", None)

        result = [gateway]
        if next_element:
            result.extend(
                self._build_structure_recursive(next_element, stop_at, visited)
            )
        return result

    def _is_parallel_gateway(self, gateway_id: str) -> bool:
        return (
            self.elements[gateway_id]["type"] == BPMNElementType.PARALLEL_GATEWAY.value
        )

    def _build_parallel_gateway(
        self,
        gateway_id: str,
        stop_at: Optional[str],
        visited: set[str],
    ) -> list[dict[str, Any]]:
        """Assemble the parallel gateway with each branch expanded up to its matching join."""
        gateway = self.elements[gateway_id].copy()
        gateway["branches"] = []

        outgoing_flows = self._get_outgoing_flows(gateway_id)
        join_element = self._find_common_branch_endpoint(gateway_id)

        if (
            not join_element
            or not self._is_parallel_gateway(join_element)
            or len(self._get_outgoing_flows(join_element)) != 1
        ):
            raise ValueError("Parallel gateway must have a corresponding join gateway")

        for flow in outgoing_flows:
            branch = self._build_structure_recursive(
                flow["target"], stop_at=join_element, visited=visited.copy()
            )
            gateway["branches"].append(branch)

        result = [gateway]
        join_outgoing_flows = self._get_outgoing_flows(join_element)
        next_element = join_outgoing_flows[0]["target"]
        result.extend(self._build_structure_recursive(next_element, stop_at, visited))
        return result

    def _get_flow_for_branch(
        self,
        gateway_id: str,
        branch: dict[str, Any],
        outgoing_flows: Optional[list[dict[str, str]]] = None,
    ) -> Optional[dict[str, str]]:
        flows = outgoing_flows or self._get_outgoing_flows(gateway_id)
        branch_condition = branch.get("condition")
        if branch_condition is not None:
            for flow in flows:
                if flow["condition"] == branch_condition:
                    return flow

        if branch.get("is_default"):
            default_flow_id = self.elements[gateway_id].get("default_flow")
            if default_flow_id:
                for flow in flows:
                    if flow["id"] == default_flow_id:
                        return flow

        branch_path = branch.get("path", [])
        if branch_path:
            target_id = branch_path[0]["id"]
            for flow in flows:
                if flow["target"] == target_id:
                    return flow

        if len(flows) == 1:
            return flows[0]

        return None

    def _handle_nested_gateway_branch(
        self,
        *,
        branch: dict[str, Any],
        last_element: dict[str, Any],
        last_outgoing_flows: list[dict[str, str]],
        common_branch_endpoint: Optional[str],
    ) -> None:
        if not last_element.get("has_join"):
            for sub_branch in last_element["branches"]:
                sub_flow = self._get_flow_for_branch(
                    last_element["id"], sub_branch, last_outgoing_flows
                )
                if sub_flow is None:
                    raise ValueError(
                        f"Unable to resolve sequence flow for branch originating from {last_element['id']}"
                    )
                self._populate_branch_transitions(
                    branch=sub_branch,
                    branch_path=sub_branch.get("path", []),
                    flow=sub_flow,
                    common_branch_endpoint=common_branch_endpoint,
                )
            return

        join_id = self._find_common_branch_endpoint(last_element["id"])
        error_messages = {
            BPMNElementType.EXCLUSIVE_GATEWAY.value: "Exclusive gateway should have a corresponding join gateway",
            BPMNElementType.INCLUSIVE_GATEWAY.value: "Inclusive gateway should have a corresponding join gateway",
        }
        if join_id is None:
            raise ValueError(error_messages[last_element["type"]])

        join_outgoing_flows = self._get_outgoing_flows(join_id)
        if len(join_outgoing_flows) != 1:
            raise ValueError("Join gateway should have one outgoing flow")

        join_target = join_outgoing_flows[0]["target"]
        if join_target != common_branch_endpoint:
            branch["next"] = join_target

    def _get_gateway_handler(
        self, element_type: str
    ) -> Optional[Callable[[str, Optional[str], set[str]], list[dict[str, Any]]]]:
        """Return the handler responsible for building the structure of the given gateway type."""
        handlers: dict[str, Callable[[str, Optional[str], set[str]], list[dict[str, Any]]]] = {
            BPMNElementType.EXCLUSIVE_GATEWAY.value: self._build_exclusive_gateway,
            BPMNElementType.INCLUSIVE_GATEWAY.value: self._build_inclusive_gateway,
            BPMNElementType.PARALLEL_GATEWAY.value: self._build_parallel_gateway,
        }
        return handlers.get(element_type)
