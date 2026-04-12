# Zombuild
# Copyright (C) 2026 Chris Bode and Zombuild Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Iterable
from typing import override
from typing import Protocol
from typing import runtime_checkable
from typing import TYPE_CHECKING

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
