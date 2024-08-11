from copy import deepcopy
from typing import Optional

from bpmn_assistant.core.exceptions import (
    ElementNotFoundException,
    ElementAlreadyExistsError,
    GatewayUpdateError,
)
from .helpers import find_position, get_all_ids, find_branch_position


def delete_element(process: list[dict], element_id: str) -> dict:
    ids = get_all_ids(process)

    if element_id not in ids:
        raise ElementNotFoundException(f"Element with id {element_id} does not exist")

    process_copy = deepcopy(process)

    position = find_position(process_copy, before_id=element_id)

    current = process_copy

    for path_element in position.path[:-1]:
        current = current[path_element]

    if position.path:
        removed_element = current[position.path[-1]].pop(position.index)
    else:
        removed_element = current.pop(position.index)

    if removed_element is None:
        raise ElementNotFoundException("Could not find the element to remove")

    return {
        "process": process_copy,
        "removed_element": removed_element,
    }


def redirect_branch(process: list[dict], branch_condition: str, next_id: str) -> dict:
    process_copy = deepcopy(process)

    position = find_branch_position(process_copy, branch_condition)

    current = process_copy

    for path_element in position.path:
        current = current[path_element]

    branch = current[position.index]

    branch["next"] = next_id

    return {
        "process": process_copy,
        "redirected_branch": branch,
    }


def validate_params(ids: list[str], before_id: Optional[str], after_id: Optional[str]):
    """
    Validate the parameters for placing an element within the process.
    """
    if before_id is not None and before_id not in ids:
        raise ElementNotFoundException(f"Element with id {before_id} does not exist")
    elif after_id is not None and after_id not in ids:
        raise ElementNotFoundException(f"Element with id {after_id} does not exist")
    elif before_id is not None and after_id is not None:
        raise ValueError("Only one of before_id and after_id can be specified")
    elif before_id is None and after_id is None:
        raise ValueError("At least one of before_id and after_id must be specified")


def add_element(
    process: list[dict],
    element: dict,
    before_id: Optional[str] = None,
    after_id: Optional[str] = None,
) -> dict:
    ids = get_all_ids(process)

    if element["id"] in ids:
        raise ElementAlreadyExistsError(
            f"Element with id {element['id']} already exists"
        )

    validate_params(ids, before_id, after_id)

    position = find_position(process, before_id=before_id, after_id=after_id)

    process_copy = deepcopy(process)

    current = process_copy

    for path_element in position.path[:-1]:
        current = current[path_element]

    if position.path:
        target_list = current[position.path[-1]]
    else:
        target_list = current

    target_list.insert(position.index, element)

    return {
        "process": process_copy,
        "added_element": element,
    }


def move_element(
    process: list[dict],
    element_id: str,
    before_id: Optional[str] = None,
    after_id: Optional[str] = None,
) -> dict:
    ids = get_all_ids(process)

    if element_id not in ids:
        raise ElementNotFoundException(f"Element with id {element_id} does not exist")

    validate_params(ids, before_id, after_id)

    process_copy, removed_element = delete_element(process, element_id).values()

    # Remove the 'next' field from the removed element
    removed_element.pop("next", None)

    process_copy, added_element = add_element(
        process_copy, removed_element, before_id, after_id
    ).values()

    return {
        "process": process_copy,
        "moved_element": added_element,
    }


def update_element(process: list[dict], new_element: dict) -> dict:
    """
    Update an element in the process. The element does not have to contain the 'next' field, as it will be
    automatically set to the next element in the process.
    The id of the element has to exist in the process.
    """
    ids = get_all_ids(process)

    if new_element["id"] not in ids:
        raise ElementNotFoundException(
            f"Element with id {new_element['id']} does not exist"
        )
    elif new_element["type"] in [
        "exclusiveGateway",
        "parallelGateway",
    ]:
        raise GatewayUpdateError("Cannot update a gateway element")

    process_copy = deepcopy(process)

    position = find_position(process_copy, before_id=new_element["id"])

    element_to_update = None

    # If path is not empty list, we need to find the list that the path is referring to
    if position.path:
        current = process_copy
        for i, path_element in enumerate(position.path):
            is_last_path_element = i == len(position.path) - 1
            if is_last_path_element:
                # Enter into the final segment of the path
                current = current[path_element]

                element_to_update = current[position.index]

                # Copy the 'next' field of the element to update
                new_element["next"] = element_to_update["next"]

                # Update the element
                current[position.index] = new_element
            else:
                # We're still navigating the path
                current = current[path_element]
    else:
        # If path is empty, we're updating at the top level
        element_to_update = process_copy[position.index]

        # Copy the 'next' field of the element to update
        new_element["next"] = element_to_update["next"]

        # Update the element
        process_copy[position.index] = new_element

    if element_to_update is None:
        raise ElementNotFoundException("Could not find the element to update")

    return {
        "process": process_copy,
        "updated_element": new_element,
    }
