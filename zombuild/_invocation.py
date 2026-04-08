from typing import Sequence
from warnings import warn
from dataclasses import dataclass
from pathlib import Path

from zombuild import paths
from zombuild._invocation_base import InvocationBase
from zombuild.tasks._default import LifecycleTask
from zombuild.tasks._task import LifecycleTaskSpecifier

from ._exception import ZombuildException, unhandled_exception_reporter
from ._package import resolve_package
from .console import Console, Indent, Style, Text

from .tasks import (
    ZombuildTask,
    ActionableTaskSpecifier,
    FuzzyTaskPredicate,
    TaskNameFilter,
    TaskPredicate,
)

from .config import PackageModel, TaskConfig
from .theme import Theme

from ._arguments import ZombuildArguments
from ._invocation_plugins import InvocationPlugins


class Tasks(InvocationBase):

    def __init__(self) -> None:
        self._tasks: list[ZombuildTask] = []
        self._lifecycle: dict[str, LifecycleTask] = dict()

    @property
    def tasks(self):
        return self._tasks

    def resolve_task(self, filter: str | TaskPredicate, fuzzy=False):

        fuzzy_predicate: TaskPredicate | None = None

        if isinstance(filter, str):
            if fuzzy:
                fuzzy_predicate = FuzzyTaskPredicate(filter)
            filter = TaskNameFilter(task_name=filter)

        matched: list[ZombuildTask] = []
        matched_fuzzy: list[ZombuildTask] = []

        for task in self._tasks:
            if filter.test(task.specifier):
                matched.append(task)
            if fuzzy_predicate is None or fuzzy_predicate.test(task.specifier):
                matched_fuzzy.append(task)

        if len(matched) == 1:
            return matched[0]
        elif len(matched_fuzzy) == 1:
            return matched_fuzzy[0]
        elif len(matched) <= 0:

            return None
        elif len(matched) > 1:
            e = ZombuildException(
                f"ambiguous task name: {filter} (matched {len(matched)} tasks)"
            )
            for m in matched:
                e.add_note(f"matched: {m}")
            raise e

    def init_tasks(self):

        for task_name in self.config.tasks:
            task_config = self.config.tasks[task_name]

            if isinstance(task_config, str):
                task_config = TaskConfig(type=task_config)

            result = self.create_task(
                prototype=task_config.type,
                name=task_name,
                args=task_config.model_extra or {},
            )

            assert result is not None

    def lifecycle_task(self, name: str) -> LifecycleTask:
        if name in self._lifecycle:
            return self._lifecycle[name]
        task = LifecycleTask(invocation=self, name=name)
        self._lifecycle[name] = task
        self._tasks.append(task)
        return task

    def create_task(self, *, prototype: str, name: str, args: dict):

        [plugin_name, prototype_name] = prototype.split(".", 1)

        task = self.loader.create_task(
            plugin_name=plugin_name,
            prototype_name=prototype_name,
            task_name=name,
            args=args,
        )

        self.register_task(task)
        return task

    def register_task[T: ZombuildTask](self, task: T) -> T:
        self._tasks.append(task)
        return task

    def _require_resolve(self, name: str | ZombuildTask, fuzzy=False):
        if isinstance(name, str):
            resolved = self.resolve_task(name, fuzzy=fuzzy)
            if resolved is None:
                raise ZombuildException(f"no such task: {name}")
            return resolved
        else:
            return name

    def collect_tasks(
        self, tasks: Sequence[str | ZombuildTask], fuzzy=False
    ) -> set[ZombuildTask]:
        """
        collects all named tasks and their dependencies

        Parameters
        ----------
        task_names : list[str]
            names of tasks

        Returns
        -------
        set[ZombuildTask]
            set of named tasks and their dependencies
        """

        def resolve(name: str | ZombuildTask):
            return self._require_resolve(name, fuzzy=fuzzy)

        queue = set(map(resolve, tasks))
        seen = set(queue)

        while len(queue) > 0:
            task = queue.pop()
            required = task.get_dependencies(self.tasks, include_optional=False)

            for other in required:
                if not other in seen:
                    queue.add(other)
                    seen.add(other)
        return seen

    def solve_tasks(self, tasks: Sequence[str | ZombuildTask], fuzzy=False):
        unsorted = list(self.collect_tasks(tasks, fuzzy=fuzzy))
        order: list[ZombuildTask] = []

        while len(unsorted) > 0:
            for candidate in unsorted:
                if not candidate.get_dependencies(unsorted, include_optional=True):
                    unsorted.remove(candidate)
                    order.append(candidate)
                    break
            else:
                raise ZombuildException("cyclic dependency detected", unsorted)

        return order

    def execute_tasks(self, tasks: Sequence[str | ZombuildTask]):
        order = self.solve_tasks(tasks, fuzzy=True)
        for task in order:
            self.execute_task(task)

    def execute_task(self, task: ZombuildTask):
        if not isinstance(task, LifecycleTask):
            self.console.print(
                Text("running task:", Theme.HEADING),
                Text(task.specifier.name, Theme.KEYWORD),
            )
        task.execute()


class Invocation(Tasks, InvocationBase):

    @dataclass
    class SequenceTask:
        name: str
        tasks: list[str]

    def __init__(
        self, arguments: ZombuildArguments, project: Path | PackageModel
    ) -> None:
        try:
            project = resolve_package(project)
            self._project_dir = project.source.parent
            self._arguments = arguments
            self._console = Console()
            self._config = project
            self._loader = InvocationPlugins(self)
            Tasks.__init__(self)
        except Exception as e:
            unhandled_exception_reporter(e)

    @property
    def arguments(self) -> ZombuildArguments:
        return self._arguments

    @property
    def console(self):
        return self._console

    @property
    def loader(self):
        return self._loader

    @property
    def config(self):
        return self._config

    @property
    def project_dir(self):
        return self._project_dir

    def execute_setup(self):
        self.loader.init_plugins()
        self.init_tasks()

        self.loader.setup_plugins()
        for task in self._tasks:
            task.setup(self)

    def execute_run(self):
        self.execute_tasks(self.arguments.tasks)

    def execute_list(self):
        c = self.console

        c.print()
        c.print(Text("Supertasks:", Theme.HEADING))

        for task in self._tasks:
            specifier = task.specifier
            if isinstance(specifier, LifecycleTaskSpecifier):
                txt_name = Text(specifier.name, Theme.KEYWORD)

                c.print(
                    Indent(
                        txt_name,
                        2,
                    )
                )

        c.print()
        c.print(Text("Tasks:", Theme.HEADING))

        for task in self._tasks:
            specifier = task.specifier
            if isinstance(specifier, ActionableTaskSpecifier):
                txt_type = Text(specifier.prototype)
                txt_name = Text(specifier.name, Theme.KEYWORD)

                c.print(
                    Indent(
                        Text.assemble(txt_name, " (", txt_type, ")"),
                        2,
                    )
                )

        if self.arguments.list_types:
            c.print()
            c.print(Text("Task Types:", Theme.HEADING))
            for plugin in self.loader.plugins:
                for factory in plugin.task_prototypes:
                    t = Text()
                    t.append(plugin.id)
                    t.append(".")
                    t.append(factory)
                    c.print(Indent(t, 2))

    def execute(self):
        try:
            command = self.arguments.command

            self.execute_setup()

            if command == "list":
                self.execute_list()
            elif command == "run":
                self.execute_run()
            elif command in ("", None):
                raise ZombuildException(f"missing command; try: `zombuild list`")
            else:
                raise ZombuildException(f'unknown command: "{command}"')
        except Exception as e:
            unhandled_exception_reporter(e)
