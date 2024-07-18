from typing import Optional

from bpmn_assistant.services.process_editing.position import Position


def get_all_ids(process: list):
    """
    Get all the ids in the process, including the ids of the branches of gateways.
    Args:
        process: The process in JSON format.
    Returns:
        list: A list of all the ids in the process.
    """
    ids = []
    for element in process:
        ids.append(element["id"])
        if element["type"] == "exclusiveGateway":
            for branch in element["branches"]:
                ids += get_all_ids(branch["path"])
        elif element["type"] == "parallelGateway":
            for branch in element["branches"]:
                ids += get_all_ids(branch)
    return ids


def find_position_in_process(
    process: list, target_id: str, after: bool = False, path: Optional[list] = None
) -> dict | None:
    """
    Recursively find the position of the target_id in the process.
    Args:
        process: The process in JSON format.
        target_id: The id of the target element.
        after: A boolean indicating whether to find the position after the target_id.
        path: The path to the current process.
    Returns:
        dict: A dictionary containing the position and path of the target_id.
    """
    path = path or []
    for index, element in enumerate(process):
        current_path = path + [index]
        if element["id"] == target_id:
            return {"index": index + 1 if after else index, "path": path}
        if element["type"] == "exclusiveGateway":
            for branch_index, branch in enumerate(element["branches"]):
                result = find_position_in_process(
                    branch["path"],
                    target_id,
                    after,
                    current_path + ["branches", branch_index, "path"],
                )
                if result:
                    return result
        elif element["type"] == "parallelGateway":
            for branch_index, branch in enumerate(element["branches"]):
                result = find_position_in_process(
                    branch, target_id, after, current_path + ["branches", branch_index]
                )
                if result:
                    return result
    return None


def find_position(
    process: list, before_id: Optional[str] = None, after_id: Optional[str] = None
) -> Position:
    """
    Find the position to insert a new element based on the before_id or after_id.
    Args:
        process: The original process.
        before_id: The id of the element before which the new element should be inserted.
        after_id: The id of the element after which the new element should be inserted.
    Returns:
        Position: A class that contains the index and path of the element.
        Example: Position(index=2, path=[0, "branches", 1, "path"])
    """
    ids = get_all_ids(process)

    position = None

    if before_id is None and after_id is None:
        raise Exception("Both before_id and after_id cannot be None")
    elif before_id is not None and after_id is not None:
        raise Exception("Only one of before_id and after_id can be specified")
    elif before_id is not None:
        if before_id not in ids:
            raise Exception(f"Element with id {before_id} does not exist")
        position = find_position_in_process(process, before_id)
    elif after_id is not None:
        if after_id not in ids:
            raise Exception(f"Element with id {after_id} does not exist")
        position = find_position_in_process(process, after_id, after=True)

    assert position is not None, "Position should not be None"

    return Position(position["index"], position["path"])
