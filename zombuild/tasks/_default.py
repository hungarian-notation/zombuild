from typing import TYPE_CHECKING, Callable, Iterable
from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path
from zombuild._exception import ZombuildException
from zombuild._invocation_base import InvocationBase
from zombuild.theme import Theme
from zombuild.console import Indent, Style, Text
from zombuild.tasks._task import (
    ActionableTaskSpecifier,
    LifecycleTaskSpecifier,
    TaskSpecifier,
    ZombuildTask,
)

from zombuild.tasks._filter import CallablePredicate, TaskPredicate

if TYPE_CHECKING:
    from zombuild import Invocation
    from zombuild.config import PackageModel


class _DefaultTaskMeta(ABCMeta):
    @property
    def prototype(cls):
        return cls.__name__


class DefaultTask(ABC, metaclass=_DefaultTaskMeta):
    """
    A general implementation of the ZombuildTask protocol that mainly handles dependency
    management, leaving execution details to subclasses.
    """

    def __init__(self, *, invocation: InvocationBase, specifier: TaskSpecifier) -> None:
        super().__init__()
        self._invocation = invocation
        self._dependencies: set[TaskPredicate] = set()
        self._optional_dependencies: set[TaskPredicate] = set()
        self._didwork = False
        self._specifier = specifier

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
        c = self.invocation.console

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
        if not self.arguments.dry_run:
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
    def specifier(self) -> TaskSpecifier:
        return self._specifier

    @property
    def invocation(self) -> InvocationBase:
        return self._invocation

    @property
    def arguments(self):
        return self.invocation.arguments

    @property
    def config(self) -> PackageModel:
        return self._invocation.config

    @property
    def project(self) -> Path:
        return self._invocation.project_dir

    def _collect(
        self,
        tasks: Iterable[ZombuildTask],
        filters: Iterable[TaskPredicate],
        out: set[ZombuildTask],
    ):
        for task in tasks:
            for filter in filters:
                if filter.test(task.specifier):
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

    def depends_on(self, other: TaskPredicate | ZombuildTask, optional: bool = False):
        if isinstance(other, DefaultTask | ZombuildTask):
            other_task = other
            other = CallablePredicate(lambda task: task == other_task.specifier)
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
        return f"{self.specifier}"

    @abstractmethod
    def execute(self) -> None: ...


class ActionableTask(DefaultTask):
    def __init__(self, *, invocation: Invocation, name: str, **extra) -> None:
        super().__init__(
            invocation=invocation,
            specifier=ActionableTaskSpecifier(
                name=name,
                prototype=self.__class__.__name__,
            ),
        )

        self._warn_extra(name, extra)

    def setup(self, invocation: Invocation) -> None:
        pass


class LifecycleTask(DefaultTask):

    def __init__(self, *, invocation: InvocationBase, name: str, **extra) -> None:
        super().__init__(
            invocation=invocation,
            specifier=LifecycleTaskSpecifier(name=name),
        )

        self._warn_extra(name, extra)

    def execute(self) -> None: ...

    def setup(self, invocation: InvocationBase) -> None:
        pass
