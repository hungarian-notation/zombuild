from typing import Iterable
from typing import overload

from zombuild.composite.component import Composite
from zombuild.composite.types import CollectComponentTarget
from zombuild.composite.types import Component
from zombuild.functional_helpers import Predicate
from zombuild.functional_helpers import TypeIsPredicate
from zombuild.functional_helpers import accept_typeis


def transform_predicate(predicate: type | Predicate | None = None):
    if predicate is None:
        return accept_typeis(Component)
    elif isinstance(predicate, type):
        return accept_typeis(predicate)
    else:
        return predicate


def _expand_component(source: Component | Composite):
    if isinstance(source, Component):
        yield source
    if isinstance(source, Composite):
        yield from source.components


def _expand_components(source: Component | Composite | Iterable[Component | Composite]):
    if isinstance(source, Component):
        yield source
    if isinstance(source, Composite):
        yield from source.components
    if isinstance(source, Iterable):
        yield from (
            iterated
            for iterated in source
            if isinstance(iterated, Component | Composite)
        )


@overload
def components[T: Component](
    source: CollectComponentTarget,
    /,
    *,
    predicate: type[T] | TypeIsPredicate[T],
) -> Iterable[T]: ...


@overload
def components(
    source: CollectComponentTarget,
    /,
    *,
    predicate: Predicate,
) -> Iterable[Component]: ...


@overload
def components(
    source: CollectComponentTarget,
    /,
    *,
    predicate: None = None,
) -> Iterable[Component]: ...


def components(
    source: CollectComponentTarget,
    /,
    *,
    predicate: type | Predicate | None = None,
) -> Iterable[Component]:
    predicate = transform_predicate(predicate)
    return (item for item in _expand_component(source) if predicate(item))


@overload
def components_collect[T: Component](
    collection_target: Iterable[CollectComponentTarget],
    /,
    *,
    predicate: type[T] | TypeIsPredicate[T],
) -> Iterable[T]: ...


@overload
def components_collect(
    collection_target: Iterable[CollectComponentTarget],
    /,
    *,
    predicate: Predicate | None = None,
) -> Iterable[Component]: ...


def components_collect(
    collection_target: Iterable[CollectComponentTarget],
    /,
    *,
    predicate: type | Predicate | None = None,
) -> Iterable[Component]:
    predicate = transform_predicate(predicate)
    targets = (target for target in collection_target)
    expanded = (y for x in targets for y in components(x) if predicate(y))

    return expanded
