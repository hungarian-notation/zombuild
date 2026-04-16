from typing import Any
from typing import Callable
from typing import Iterable
from typing import TypeGuard
from typing import overload

from zombuild.composite._collect_components import components_collect
from zombuild.composite.component import Component
from zombuild.composite.component import Composite


class ComponentAccessorsMixin(Composite):
    @overload
    def where[T](self, type: type[T], /) -> Iterable[T]: ...

    @overload
    def where[T: Component](
        self, typeguard: Callable[[Component], TypeGuard[T]], /
    ) -> Iterable[T]: ...

    @overload
    def where(
        self, predicate: Callable[[Component], bool], /
    ) -> Iterable[Component]: ...

    def where(self, predicate: type | Callable[[Component], bool], /) -> Iterable[Any]:
        return components_collect(self.components, predicate=predicate)

    @overload
    def get[T](self, type: type[T], /) -> T | None: ...

    @overload
    def get[T: Component](
        self, typeguard: Callable[[Component], TypeGuard[T]], /
    ) -> T | None: ...

    @overload
    def get(self, predicate: Callable[[Component], bool], /) -> Component | None: ...

    def get(self, predicate: type | Callable[[Any], bool]) -> Any:
        return next(iter(self.where(predicate)), None)

    def has(self, predicate: type | Callable[[Component], bool]):
        return any(self.where(predicate))
