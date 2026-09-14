from bpmn_assistant.core.exceptions import ElementNotFoundException, ProcessException
from bpmn_assistant.services.process_traversal import (
    ElementLocation, find_element, walk_elements,
)


def get_all_ids(process: list[dict]) -> list[str]:
    return [location.element['id'] for location in walk_elements(process)]


def require_element(process: list[dict], element_id: str) -> ElementLocation:
    location = find_element(process, element_id)
    if location is None:
        raise ElementNotFoundException(f'Element with id {element_id} does not exist')
    return location


def find_branch(process: list[dict], condition: str) -> dict:
    # Preserve first-match behavior; conditions are not unique branch identifiers.
    for location in walk_elements(process):
        element = location.element
        if element['type'] in ('exclusiveGateway', 'inclusiveGateway'):
            for branch in element['branches']:
                if 'condition' in branch and branch['condition'] == condition:
                    return branch
    raise ProcessException(f"Branch with condition '{condition}' does not exist")
