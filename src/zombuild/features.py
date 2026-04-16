from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Sequence
from typing import TypeGuard
from typing import overload
from typing import override

from zombuild.setup_mixin import SetupMixin

if TYPE_CHECKING:
    from zombuild._invocation import Invocation


class Feature[T: Features = Features](ABC, SetupMixin):
    def __init__(self, provider: T) -> None:
        self._provider = provider
        super().__init__()

    @property
    def provider(self) -> T:
        return self._provider


class Features(ABC):
    @property
    @abstractmethod
    def features(self) -> list[Feature]: ...


def typeguard[T](guard: type[T]) -> Callable[[Any], TypeGuard[T]]:
    def closure(value: Any) -> TypeGuard[T]:
        return isinstance(value, guard)

    return closure


class FeatureAccessors(Features):
    @overload
    def get_feature[T](self, type: type[T], /) -> T | None: ...

    @overload
    def get_feature[T: Feature](
        self, typeguard: Callable[[Feature], TypeGuard[T]], /
    ) -> T | None: ...

    @overload
    def get_feature(
        self, predicate: Callable[[Feature], bool], /
    ) -> Feature | None: ...

    def get_feature(self, predicate: type | Callable[[Any], bool]) -> Any:

        if isinstance(predicate_type := predicate, type):
            predicate = typeguard(predicate_type)

        for attr in self.features:
            if predicate(attr):
                return attr
        else:
            return None

    @overload
    def get_features[T](self, type: type[T], /) -> Sequence[T]: ...

    @overload
    def get_features[T: Feature](
        self, typeguard: Callable[[Feature], TypeGuard[T]], /
    ) -> Sequence[T]: ...

    @overload
    def get_features(
        self, predicate: Callable[[Feature], bool], /
    ) -> Sequence[Feature]: ...

    def get_features(
        self, predicate: type | Callable[[Feature], bool], /
    ) -> Sequence[Any]:
        if isinstance(predicate, type):
            return [attr for attr in self.features if isinstance(attr, predicate)]
        else:
            return [attr for attr in self.features if predicate(attr)]

    def has_feature(self, predicate: type | Callable[[Feature], bool]):
        return len(self.get_features(predicate)) > 0


@dataclass
class DefaultTaskFeature(Feature):
    create_tasks: Callable[[Invocation], None]
    wire_tasks: Callable[[Invocation], None] | None = None

    @override
    def setup(self, invocation: Invocation):
        self.create_tasks(invocation)

    @override
    def setup_late(self, invocation: Invocation):
        if self.wire_tasks:
            self.wire_tasks(invocation)
