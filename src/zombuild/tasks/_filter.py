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

import re
from typing import TYPE_CHECKING
from typing import Callable
from typing import Protocol

if TYPE_CHECKING:
    from zombuild.tasks._task import TaskSpecifier


class TaskPredicate(Protocol):
    def test(self, other: TaskSpecifier) -> bool: ...


class CallablePredicate[T]:
    def __init__(self, callable: Callable[[T], bool]) -> None:
        self.callable = callable

    def test(self, other: T) -> bool:
        return self.callable(other)


class TaskNameFilter(TaskPredicate):
    def __init__(self, task_name: str | None) -> None:
        super().__init__()
        self.__task_name = task_name

    def test(self, other: TaskSpecifier):
        return self.__task_name is None or self.__task_name == other.name

    def __str__(self) -> str:
        return f"*:{self.__task_name or '*'}"


def _fuzzy_pattern(string: str):
    """
    returns a regex pattern that matches strings that could be formed from the input
    string by insertion of missing characters
    """
    return "^.*" + ".*".join(map(re.escape, string)) + ".*$"


class FuzzyTaskPredicate(TaskPredicate):
    """
    TaskPredicate that matches tasks whose names are fuzzy-equal to a test string.
    """

    def __init__(self, name) -> None:
        self._name = name
        self._pattern = _fuzzy_pattern(name)

    def test(self, other: TaskSpecifier) -> bool:
        result = re.match(self._pattern, other.name) is not None
        return result

    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return repr(self._pattern)
