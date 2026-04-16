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
from typing import Iterable

from zombuild.composite.component import Composite
from zombuild.functional_helpers import Predicate


class ZombuildTask(Composite, ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get_dependencies(
        self,
        tasks: Iterable[ZombuildTask],
        include_optional: bool = False,
    ) -> set[ZombuildTask]:
        raise NotImplementedError()

    @abstractmethod
    def depends_on(
        self,
        other: Predicate[ZombuildTask] | ZombuildTask,
        optional: bool = False,
    ): ...

    @abstractmethod
    def execute(self) -> None:
        raise NotImplementedError()
