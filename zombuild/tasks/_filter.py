from operator import call
import re
from typing import TYPE_CHECKING, Callable, Protocol

if TYPE_CHECKING:
    from zombuild.tasks._task import TaskSpecifier, ZombuildTask


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
        return f"*:{self.__task_name or "*"}"


def _fuzzy_pattern(string: str):
    """
    returns a regex pattern that matches strings that could be formed from the input string by
    insertion of missing characters
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
