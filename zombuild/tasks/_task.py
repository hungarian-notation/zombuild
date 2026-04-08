from abc import ABC
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Protocol, runtime_checkable

from zombuild.tasks._filter import TaskPredicate


if TYPE_CHECKING:
    from zombuild import Invocation


@dataclass(frozen=True)
class TaskSpecifier(ABC):

    name: str


@dataclass(frozen=True)
class ActionableTaskSpecifier(TaskSpecifier):

    prototype: str

    def __str__(self) -> str:
        return f"{self.prototype}.{self.name}"


@dataclass(frozen=True)
class LifecycleTaskSpecifier(TaskSpecifier):

    @property
    def group(self):
        return "@"

    def __str__(self) -> str:
        return f"@{self.name}"


@runtime_checkable
class ZombuildTask(Protocol):

    def __init__(self, *, name: str, invocation: Invocation, **kwargs) -> None: ...

    @property
    def specifier(self) -> TaskSpecifier: ...

    def get_dependencies(
        self,
        tasks: Iterable[ZombuildTask],
        include_optional: bool = False,
    ) -> set[ZombuildTask]: ...

    def depends_on(
        self,
        other: TaskPredicate | ZombuildTask,
        optional: bool = False,
    ): ...

    def setup(self, invocation: Invocation) -> None:
        """
        Called after all tasks have been created, but before execution begins. 

        Args:
            invocation (Invocation): _description_
        """
        ...

    def execute(self) -> None: ...
