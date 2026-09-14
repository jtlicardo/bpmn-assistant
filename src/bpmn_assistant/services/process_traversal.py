"""Locations in the structured process, without flattening BPMN scopes."""

from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class ElementLocation:
    """References into the input tree; locate again after changing its lists.

    scope is the process list belonging to the nearest pool or subprocess,
    or the input list for a plain process. Branches and boundary handlers
    remain in their host's scope.
    """

    container: list[dict]
    index: int
    scope: list[dict]

    @property
    def element(self) -> dict:
        return self.container[self.index]


def walk_elements(process: list[dict]) -> Iterator[ElementLocation]:
    """Visit stored elements in depth-first order, including attached events.

    References (next, lane IDs, message flows) are not containment edges and
    are not followed. Synthesized join gateways are not stored elements.
    """
    yield from _walk(process, process)


def _walk(container: list[dict], scope: list[dict]) -> Iterator[ElementLocation]:
    for index, element in enumerate(container):
        yield ElementLocation(container, index, scope)
        kind = element['type']
        if kind in ('pool', 'subProcess'):
            contents = element['process']
            yield from _walk(contents, contents)
        elif kind in ('exclusiveGateway', 'inclusiveGateway'):
            for branch in element['branches']:
                yield from _walk(branch['path'], scope)
        elif kind == 'parallelGateway':
            for branch in element['branches']:
                yield from _walk(branch, scope)
        elif kind == 'boundaryEvent':
            yield from _walk(element.get('path', []), scope)
        yield from _walk(element.get('boundary_events', []), scope)


def find_element(process: list[dict], element_id: str) -> ElementLocation | None:
    """Return the first stored element with this ID, or None."""
    return next(
        (location for location in walk_elements(process)
         if location.element['id'] == element_id),
        None,
    )
