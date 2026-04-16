from typing import Any
from typing import Protocol
from typing import Self
from typing import overload


class PropertyLike(Protocol):
    @overload
    def __get__(self, instance: None, owner: type, /) -> Self: ...
    @overload
    def __get__(self, instance: Any, owner: type | None = None, /) -> Any: ...
