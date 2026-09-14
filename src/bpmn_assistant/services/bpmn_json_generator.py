import xml.etree.ElementTree as ET
from collections import deque
from typing import Any, Callable, Optional

from bpmn_assistant.core.enums import BPMNElementType
from bpmn_assistant.services.bpmn_process_transformer import BpmnProcessTransformer
from bpmn_assistant.services.validate_bpmn import validate_bpmn, validate_pools
from bpmn_assistant.services.element_details import ARTIFACT_TYPES, is_link, read_artifacts, read_details


class BpmnJsonGenerator:
    """
    Class to generate the JSON representation of a BPMN process from the BPMN XML.
    """

    def __init__(self):
        self.elements: dict[str, dict[str, Any]] = {}
        self.flows: dict[str, dict[str, Any]] = {}
        self.process: list[dict[str, Any]] = []
        self.preserve_pool_metadata = False
        self.node_lanes: dict[str, str] = {}
        self.root = None

    def _find_process_element(self, root: ET.Element) -> ET.Element:
        for elem in root.iter():
            if elem.tag.endswith("process"):
                return elem
        raise ValueError("No process element found in the BPMN XML")

    def create_bpmn_json(self, bpmn_xml: str) -> list[dict[str, Any]]:
        """
        Create the JSON representation of the process from the BPMN XML
        Constraints:
            - Tasks, embedded subprocesses, timer/error boundary handlers, events, and exclusive/inclusive/parallel gateways
            - Supported event definitions are validated against each event's position
            - The process must have only one start event
            - Pools, flat lanes, and message flows are supported; nested lanes are not
            - Parallel gateways must have a corresponding join gateway
        """
        root = ET.fromstring(bpmn_xml)
        self.root = root
        ns = {'b': 'http://www.omg.org/spec/BPMN/20100524/MODEL'}
        message_flows = root.findall('./b:collaboration/b:messageFlow', ns)
        participants = root.findall('./b:collaboration/b:participant', ns)
        processes = root.findall('./b:process', ns)
        if message_flows and not participants:
            raise ValueError('Message flows require pools.')
        if participants or root.find('.//b:lane', ns) is not None or len(processes) > 1:
            return self._read_pools(participants, processes, ns, message_flows)
        process_element = self._find_process_element(root)
        if read_artifacts(process_element):
            self.preserve_pool_metadata = True
        self._get_elements_and_flows(process_element)
        start_events = [
            elem
            for elem in self.elements.values()
            if elem["type"] == BPMNElementType.START_EVENT.value
        ]
        if len(start_events) != 1:
            raise ValueError("Process must contain exactly one start event")
        self._build_process_structure()
        if any(node.get('eventDefinition') == 'linkEventDefinition' for node in self.elements.values()):
            emitted = {node['id'] for node in BpmnProcessTransformer().transform(self.process)['elements']}
            if emitted != set(self.elements):
                raise ValueError('The link events contain disconnected or unsupported process structure.')
        self.process.extend(read_artifacts(process_element))
        validate_bpmn(self.process)
        return self.process

    def _read_pools(self, participants, processes, ns, message_flows):

        by_id = {element.get('id'): element for element in processes}
        referenced = {participant.get('processRef') for participant in participants}
        if participants and any(identifier not in referenced for identifier in by_id):
            raise ValueError('Every process must belong to a pool.')
        if not participants:
            participants = [ET.Element('participant', {
                'id': f"{element.get('id')}_pool", 'name': element.get('name', ''),
                'processRef': element.get('id'),
            }) for element in processes]
        pools = []
        for participant in participants:
            process_id = participant.get('processRef')
            process_element = by_id.get(process_id)
            if process_id and process_element is None:
                raise ValueError(f'Pool references missing process: {process_id}')
            pool = {
                'type': 'pool', 'id': participant.get('id'), 'label': participant.get('name', ''),
                'process_id': process_id or f"{participant.get('id')}_process",
                'lanes': [], 'process': [],
            }
            if process_element is not None:
                generator = BpmnJsonGenerator()
                generator.root = self.root
                generator.preserve_pool_metadata = True
                for lane in process_element.findall('./b:laneSet/b:lane', ns):
                    if lane.find('b:childLaneSet', ns) is not None:
                        raise ValueError('Nested lanes are not supported yet; use flat lanes.')
                    pool['lanes'].append({'id': lane.get('id'), 'label': lane.get('name', '')})
                    for reference in lane.findall('b:flowNodeRef', ns):
                        node_id = (reference.text or '').strip()
                        if node_id in generator.node_lanes:
                            raise ValueError(f'Element belongs to multiple lanes: {node_id}')
                        generator.node_lanes[node_id] = lane.get('id')
                generator._get_elements_and_flows(process_element)
                if any(reference not in generator.elements for reference in generator.node_lanes):
                    raise ValueError('Lane refers to a missing or unsupported flow node.')
                if generator.elements:
                    starts = [node for node in generator.elements.values() if node['type'] == 'startEvent']
                    if len(starts) != 1:
                        raise ValueError('Each non-empty pool must contain exactly one start event.')
                    generator._build_process_structure()
                    pool['process'] = generator.process
                # Do not silently drop unsupported nodes or disconnected process content.
                emitted = {node['id'] for node in BpmnProcessTransformer().transform(pool['process'])['elements']}
                if emitted != set(generator.elements):
                    raise ValueError('The pool contains disconnected or unsupported process structure.')
                pool['process'].extend(read_artifacts(process_element))
                allowed = {element.value for element in BPMNElementType} | ARTIFACT_TYPES | {'sequenceFlow', 'laneSet', 'documentation'}
                if any(child.tag.split('}')[-1] not in allowed for child in process_element):
                    raise ValueError('The pool contains unsupported BPMN elements.')
            pools.append(pool)
        source_pools = {}
        for pool in pools:
            source_pools[pool['id']] = pool
            from bpmn_assistant.services.activity_support import scopes
            for _, graph in scopes(pool['process']):
                for node in graph['elements']:
                    source_pools[node['id']] = pool
        for flow in message_flows:
            pool = source_pools.get(flow.get('sourceRef'))
            if pool is None:
                raise ValueError('Message flow refers to a missing or unsupported source endpoint.')
            pool.setdefault('message_flows', []).append({
                'id': flow.get('id'), 'source_ref': flow.get('sourceRef'),
                'target_ref': flow.get('targetRef'), 'label': flow.get('name', ''),
            })
        collaboration = self.root.find('{*}collaboration')
        if collaboration is not None:
            pools.extend(read_artifacts(collaboration))
        validate_pools(pools)
        return pools

    def _remember_join(self, gateway, join_id):
        if self.preserve_pool_metadata:
            gateway['join_id'] = join_id
            if join_id in self.node_lanes:
                gateway['join_lane_id'] = self.node_lanes[join_id]

    def _build_process_structure(self):
        start_event = next(
            elem
            for elem in self.elements.values()
            if elem["type"] == BPMNElementType.START_EVENT.value
        )

        # Start building the process structure recursively from the start event
        self.process = self._build_structure_recursive(start_event["id"])
        self._attach_boundary_paths()
        if any(node['type'] in ('subProcess', 'boundaryEvent') for node in self.elements.values()):
            graph = BpmnProcessTransformer().transform(self.process)
            actual = {(flow['sourceRef'], flow['targetRef']) for flow in graph['flows']}
            expected = {(flow['source'], flow['target']) for flow in self.flows.values()}
            if {node['id'] for node in graph['elements']} != set(self.elements) or actual != expected:
                raise ValueError('Unsupported activity structure: import would change or drop nodes or connections.')

    def _attach_boundary_paths(self):
        main_ids = {node['id'] for node in BpmnProcessTransformer().transform(self.process)['elements']}
        for node in self.elements.values():
            if node['type'] != 'boundaryEvent':
                continue
            host = self.elements.get(node.get('attached_to'))
            if not host or (host['type'] != 'subProcess' and not host['type'].lower().endswith('task')):
                raise ValueError('Boundary event must attach to a task or subprocess in the same scope.')
            outgoing = self._get_outgoing_flows(node['id'])
            if len(outgoing) != 1 or any(flow['target'] == node['id'] for flow in self.flows.values()):
                raise ValueError('Boundary events require no incoming and exactly one outgoing flow.')
            target = outgoing[0]['target']
            pending, visited, rejoins = [target], set(), set()
            while pending:
                current = pending.pop()
                if current in main_ids:
                    rejoins.add(current)
                    continue
                if current in visited:
                    continue
                visited.add(current)
                pending.extend(flow['target'] for flow in self._get_outgoing_flows(current))
            if len(rejoins) > 1:
                raise ValueError('A boundary handler can currently rejoin the normal path at only one element.')
            next_id = next(iter(rejoins), None)
            boundary = {key: value for key, value in node.items() if key != 'attached_to'}
            boundary['path'] = self._build_structure_recursive(target, stop_at=next_id)
            if next_id:
                boundary['next'] = next_id
            host.setdefault('boundary_events', []).append(boundary)

    def _read_subprocess(self, element):
        if element.get('triggeredByEvent') in ('true', '1'):
            raise ValueError('Event subprocesses are not supported; use an ordinary embedded subprocess.')
        allowed = {kind.value for kind in BPMNElementType} | ARTIFACT_TYPES | {'sequenceFlow', 'documentation', 'incoming', 'outgoing'}
        if any(child.tag.split('}')[-1] not in allowed for child in element):
            raise ValueError('Unsupported embedded subprocess content (including nested lanes or loop markers).')
        generator = BpmnJsonGenerator()
        generator.root = self.root
        generator.preserve_pool_metadata = True
        generator._get_elements_and_flows(element)
        if sum(node['type'] == 'startEvent' for node in generator.elements.values()) != 1:
            raise ValueError('Embedded subprocesses require exactly one start event.')
        generator._build_process_structure()
        generator.process.extend(read_artifacts(element))
        graph = BpmnProcessTransformer().transform(generator.process)
        if {node['id'] for node in graph['elements']} != set(generator.elements) or {
            (flow['sourceRef'], flow['targetRef']) for flow in graph['flows']
        } != {(flow['source'], flow['target']) for flow in generator.flows.values()}:
            raise ValueError('Unsupported subprocess structure: import would change nodes or connections.')
        validate_bpmn(generator.process)
        return generator.process

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
            self._remember_join(gateway, common_branch_endpoint)
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
            self._remember_join(gateway, common_branch_endpoint)
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

        self._remember_join(gateway, join_element)

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

    def _is_parallel_gateway(self, gateway_id: str) -> bool:
        return (
            self.elements[gateway_id]["type"] == BPMNElementType.PARALLEL_GATEWAY.value
        )

    def _is_exclusive_gateway(self, gateway_id: str) -> bool:
        return (
            self.elements[gateway_id]["type"] == BPMNElementType.EXCLUSIVE_GATEWAY.value
        )

    def _is_inclusive_gateway(self, gateway_id: str) -> bool:
        return (
            self.elements[gateway_id]["type"] == BPMNElementType.INCLUSIVE_GATEWAY.value
        )

    def _get_outgoing_flows(self, element_id: str) -> list[dict[str, str]]:
        node = self.elements[element_id]
        if is_link(node, 'intermediateThrowEvent'):
            catches = [other for other in self.elements.values()
                       if is_link(other, 'intermediateCatchEvent')
                       and other.get('link_name') == node.get('link_name')]
            if len(catches) != 1:
                raise ValueError('Each link name must have exactly one matching catch event.')
            return [{'id': f"link_{element_id}", 'source': element_id,
                     'target': catches[0]['id'], 'condition': None}]
        return [flow for flow in self.flows.values() if flow["source"] == element_id]

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

    def _get_elements_and_flows(self, process: ET.Element):
        if any(child.tag.split('}')[-1] in ('subProcess', 'boundaryEvent') for child in process):
            self.preserve_pool_metadata = True
        labeled_elements = {
            'subProcess', 'boundaryEvent',
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
                if elem_id in self.node_lanes:
                    self.elements[elem_id]['lane_id'] = self.node_lanes[elem_id]
                if tag in labeled_elements:
                    name = elem.get("name")
                    if name:  # Only add label if name exists and is not empty
                        self.elements[elem_id]["label"] = name

                # Store default flow for inclusive/exclusive gateways
                if tag in [BPMNElementType.INCLUSIVE_GATEWAY.value, BPMNElementType.EXCLUSIVE_GATEWAY.value]:
                    default_flow = elem.get("default")
                    if default_flow:
                        self.elements[elem_id]["default_flow"] = default_flow

                read_details(elem, self.elements[elem_id], self.root)
                if tag == 'subProcess':
                    self.elements[elem_id]['label'] = elem.get('name', '')
                    self.elements[elem_id]['process'] = self._read_subprocess(elem)
                    shape = next((shape for shape in self.root.iter()
                                  if shape.tag.endswith('BPMNShape') and shape.get('bpmnElement') == elem_id), None)
                    self.elements[elem_id]['expanded'] = shape.get('isExpanded', 'false') in ('true', '1') if shape is not None else True
                elif tag == 'boundaryEvent':
                    self.elements[elem_id]['attached_to'] = elem.get('attachedToRef')
                    self.elements[elem_id]['cancel_activity'] = elem.get('cancelActivity', 'true') in ('true', '1')
            elif tag == "sequenceFlow":
                self.flows[elem_id] = {
                    "id": elem_id,
                    "source": elem.get("sourceRef"),
                    "target": elem.get("targetRef"),
                    "condition": elem.get("name"),
                }
        for flow in self.flows.values():
            source = self.elements.get(flow['source'])
            target = self.elements.get(flow['target'])
            if source is None or target is None:
                raise ValueError('Sequence flow refers to a missing element or crosses a subprocess scope.')
            if source and is_link(source, 'intermediateThrowEvent') or target and is_link(target, 'intermediateCatchEvent'):
                raise ValueError('Link throw events cannot have outgoing sequence flows; link catches cannot have incoming sequence flows.')
