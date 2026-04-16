from typing import Any
from typing import Callable
from typing import Protocol
from typing import TypeIs


class Predicate[U = Any](Protocol):
    def __call__(self, arg: U, /) -> bool: ...


class TypeIsPredicate[T, U = Any](Protocol):
    def __call__(self, arg: U, /) -> TypeIs[T]: ...


def accept_typeis[T, U = Any](t: type[T]) -> Callable[[Any], TypeIs[T]]:
    def predicate(v: object) -> TypeIs[T]:
        if isinstance(v, t):
            return True
        return False

    return predicate


def accept_all(any: Any):
    return True
