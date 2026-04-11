from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Protocol, override, runtime_checkable

from zombuild.lifecycle_mixins import WithSetupLifecycle
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


class ZombuildTask(ABC, WithSetupLifecycle["Invocation"]):

    @property
    @abstractmethod
    def specifier(self) -> TaskSpecifier: ...

    @abstractmethod
    def get_dependencies(
        self,
        tasks: Iterable[ZombuildTask],
        include_optional: bool = False,
    ) -> set[ZombuildTask]: ...

    @abstractmethod
    def depends_on(
        self,
        other: TaskPredicate | ZombuildTask,
        optional: bool = False,
    ): ...

    @abstractmethod
    def execute(self) -> None: ...
