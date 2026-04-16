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

from abc import ABCMeta
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Callable
from typing import Iterable

from zombuild._context import context
from zombuild._context import context_arguments
from zombuild.composite.component import Composite
from zombuild.composite.component import EmptyComponents
from zombuild.composite.component import MutableComponents
from zombuild.console import Indent
from zombuild.console import Text
from zombuild.functional_helpers import Predicate
from zombuild.tasks._task import ZombuildTask
from zombuild.theme import Theme

if TYPE_CHECKING:
    from zombuild import Invocation


class _DefaultTaskMeta(ABCMeta):
    @property
    def prototype(cls):
        return cls.__name__


def equality_predicate(value: object):
    return lambda other: other == value


class DefaultTask(ZombuildTask, metaclass=_DefaultTaskMeta):
    """
    A general implementation of the ZombuildTask protocol that mainly handles dependency
    management, leaving execution details to subclasses.
    """

    def __init__(self, *, name: str) -> None:
        self._dependencies: set[Predicate[ZombuildTask]] = set()
        self._optional_dependencies: set[Predicate[ZombuildTask]] = set()
        self._didwork = False
        self._name = name

    @classmethod
    def _warn_extra(cls: type, name: str, extra: dict[str, object]):
        if len(extra) > 0:
            t1 = Text("extra arguments:", Theme.WARNING)
            t2 = Text(cls.__name__)
            t3 = Text(name) + ":"
            print(t1, t2, t3, ", ".join(extra.keys()))

    def log_info(self, *message: object, indent=2):
        self.invocation.info(Indent(" ".join(map(str, message)), indent))

    def log_verbose(self, *message: object, indent=2):
        self.invocation.verbose(Indent(" ".join(map(str, message)), indent))

    def log_trace(self, *message: object, indent=2):
        self.invocation.trace(Indent(" ".join(map(str, message)), indent))

    def log_work(self, work_type: str, **kwargs):
        self.log_verbose(Text(work_type))
        self.log_trace()
        for k in kwargs:
            self.log_trace(
                Text(k) + "\t" + Text(str(kwargs[k]), Theme.TRACE_ITALIC),
                indent=4,
            )
        self.log_trace()

        self._didwork = True

    def perform_work[T](
        self, work: Callable[[], T], work_type: str, **kwargs
    ) -> T | None:
        result = None
        if not context.get().arguments.dry_run:
            try:
                result = work()
            except Exception as e:
                e.add_note(f"while attempting to perform work: {work_type}")
                for k in kwargs:
                    e.add_note(f"\t{k} = {repr(kwargs[k])}")
                raise
        self.log_work(work_type, **kwargs)
        return result

    @classmethod
    def get_prototype(cls) -> str:
        return cls.__name__

    @property
    def name(self) -> str:
        return self._name

    @property
    def invocation(self) -> Invocation:
        return context.get().invocation

    def _collect(
        self,
        tasks: Iterable[ZombuildTask],
        filters: Iterable[Predicate[ZombuildTask]],
        out: set[ZombuildTask],
    ):
        for task in tasks:
            for filter in filters:
                if filter(task):
                    out.add(task)
                    break

    def get_dependencies(
        self,
        tasks: Iterable[ZombuildTask],
        include_optional: bool = False,
    ) -> set[ZombuildTask]:
        matched: set[ZombuildTask] = set()
        self._collect(tasks, self._dependencies, matched)
        if include_optional:
            self._collect(tasks, self._optional_dependencies, matched)
        return matched

    def depends_on(
        self, other: Predicate[ZombuildTask] | ZombuildTask, optional: bool = False
    ):

        if context_arguments().verbose > 3:
            print("dependency", self, other, optional)

        if isinstance(other, DefaultTask | ZombuildTask):
            other = equality_predicate(other)
        if optional:
            self._optional_dependencies.add(other)
        else:
            self._dependencies.add(other)

    # @property
    # @abstractmethod
    # def inputs(self) -> TaskInputs: ...

    # @property
    # @abstractmethod
    # def outputs(self) -> TaskOutputs: ...

    def __repr__(self) -> str:
        return f"{self.name}"

    @abstractmethod
    def execute(self) -> None: ...


class ActionableTask(DefaultTask, Composite):
    def __init__(self, *, name: str, **extra) -> None:
        super().__init__(name=name)
        self._warn_extra(name, extra)

    components = MutableComponents()
    add = components.mutator()


class LifecycleTask(DefaultTask):
    def __init__(self, *, name: str, **extra) -> None:
        super().__init__(name=name)
        self._warn_extra(name, extra)

    def execute(self) -> None:
        pass

    components = EmptyComponents()
