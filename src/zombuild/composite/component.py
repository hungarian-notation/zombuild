from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Protocol
from typing import Self
from typing import cast
from typing import overload


class Component:
    pass


class Composite(ABC):
    components: ComponentsDescriptor


class ComponentsObserver(Protocol):
    def on_invalidated(self, what: ComponentsDescriptor, /): ...


VIEW_KEY = "_components_view"
VALUES_KEY = "_components_values"
SRC_KEY = "_components_sources"


def getdefault[T](obj: Composite, key: str, ctor: Callable[[Composite], T]):
    if not hasattr(obj, key):
        nvalue = ctor(obj)
        update = {key: nvalue}
        vars(obj).update(**update)
        return nvalue
    if (nvalue := getattr(obj, key)) is None:
        nvalue = ctor(obj)
        setattr(obj, key, nvalue)
    return cast(T, nvalue)


def clearattr[T](obj: Composite, key: str):
    if hasattr(obj, key):
        delattr(obj, key)


class ComponentsDescriptor(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def view(self, obj: Composite, /) -> frozenset[Component]: ...

    @overload
    def __get__(self, obj: None, objtype: type[Composite]) -> Self: ...
    @overload
    def __get__(self, obj: Composite, objtype: Any) -> frozenset[Component]: ...

    def __get__(self, obj: Composite | None, objtype: type[Composite] | None):
        if obj is None:
            return self
        else:
            return self.view(obj)


class EmptyComponents(ComponentsDescriptor):
    def view(self, obj: Composite, /) -> frozenset[Component]:
        return getdefault(obj, VIEW_KEY, lambda _: frozenset())


class DerivedComponents(ComponentsDescriptor):
    def __init__(self, provider: _Provider) -> None:
        super().__init__()
        self.__provider = provider

    # def rebuild(self, obj: Composite):
    #     return frozenset(self.__provider(obj))

    def view(self, obj: Composite, /):
        return frozenset(self.__provider(obj))

    def invalidate(self, obj):
        clearattr(obj, VIEW_KEY)


type _Provider[T: Composite] = Callable[[T], Iterable[Component]]


class MutableComponents(ComponentsDescriptor):
    def rebuild(self, obj: Composite):
        return frozenset(getdefault(obj, VALUES_KEY, lambda _: set()))

    def view(self, obj: Composite, /):
        return getdefault(obj, VIEW_KEY, self.rebuild)

    def mutator(self):
        def impl(obj: Composite, component: Component, /):
            values = getdefault(obj, VALUES_KEY, lambda _: set[Component]())
            values.add(component)

        return impl
