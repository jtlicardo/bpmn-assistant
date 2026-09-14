from copy import deepcopy
from typing import Optional

from bpmn_assistant.core.exceptions import (
    ElementAlreadyExistsError,
    ElementNotFoundException,
)

from .helpers import find_branch, get_all_ids, require_element


def delete_element(process: list[dict], element_id: str) -> dict:
    process_copy = deepcopy(process)
    location = require_element(process_copy, element_id)
    removed_element = location.container.pop(location.index)
    return {'process': process_copy, 'removed_element': removed_element}


def redirect_branch(process: list[dict], branch_condition: str, next_id: str) -> dict:
    process_copy = deepcopy(process)
    branch = find_branch(process_copy, branch_condition)
    branch['next'] = next_id
    return {'process': process_copy, 'redirected_branch': branch}


def validate_params(ids: list[str], before_id: Optional[str], after_id: Optional[str]):
    """Validate the parameters for placing an element within the process."""
    if before_id is not None and before_id not in ids:
        raise ElementNotFoundException(f'Element with id {before_id} does not exist')
    elif after_id is not None and after_id not in ids:
        raise ElementNotFoundException(f'Element with id {after_id} does not exist')
    elif before_id is not None and after_id is not None:
        raise ValueError('Only one of before_id and after_id can be specified')
    elif before_id is None and after_id is None:
        raise ValueError('At least one of before_id and after_id must be specified')


def add_element(
    process: list[dict],
    element: dict,
    before_id: Optional[str] = None,
    after_id: Optional[str] = None,
) -> dict:
    ids = get_all_ids(process)
    if element['id'] in ids:
        raise ElementAlreadyExistsError(f"Element with id {element['id']} already exists")
    validate_params(ids, before_id, after_id)

    process_copy = deepcopy(process)
    target_id = before_id if before_id is not None else after_id
    assert target_id is not None  # validate_params requires exactly one target.
    location = require_element(process_copy, target_id)
    index = location.index + (after_id is not None)
    location.container.insert(index, element)
    return {'process': process_copy, 'added_element': element}


def move_element(
    process: list[dict],
    element_id: str,
    before_id: Optional[str] = None,
    after_id: Optional[str] = None,
) -> dict:
    require_element(process, element_id)
    validate_params(get_all_ids(process), before_id, after_id)

    removed = delete_element(process, element_id)
    added = add_element(removed['process'], removed['removed_element'], before_id, after_id)
    return {'process': added['process'], 'moved_element': added['added_element']}


def update_element(process: list[dict], new_element: dict) -> dict:
    process_copy = deepcopy(process)
    location = require_element(process_copy, new_element['id'])
    location.container[location.index] = new_element
    return {'process': process_copy, 'updated_element': new_element}
