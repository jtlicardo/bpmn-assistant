"""Helpers for pool containers in structured processes."""


def has_pools(process: list) -> bool:
    return any(isinstance(element, dict) and element.get('type') == 'pool' for element in process)
