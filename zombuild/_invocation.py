from typing import Sequence, override
from warnings import warn
from dataclasses import dataclass
from pathlib import Path

from zombuild import paths
from zombuild.plugins._plugin import FeatureAccessors
from zombuild.plugins.features import PluginFeature

from ._invocation_base import InvocationBase
from .config.task import TaskConfig
from .tasks._default import LifecycleTask
from .tasks._task import LifecycleTaskSpecifier
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

from .config.package import PackageConfig
from .theme import Theme

from ._arguments import ZombuildArguments
from ._invocation_plugins import InvocationPlugins

from .lifecycle_mixins import execute_setup


class Tasks:

    def __init__(self, invocation: Invocation) -> None:
        self._tasks: list[ZombuildTask] = []
        self._lifecycle: dict[str, LifecycleTask] = dict()
        self._invocation = invocation

    @property
    def tasks(self):
        return self._tasks

    def resolve_task(
        self, filter: str | TaskPredicate, fuzzy=False
    ) -> set[ZombuildTask]:
        """
        Gets the set of tasks matched by the fiter.

        Args:
            filter: name or predicate
            fuzzy: Enable fuzzy matching.
                Allows strings to match tasks whose names contain their characters in order, ignoring
                extra intervening characters. Defaults to False.

        Returns:
            set of matched tasks
        """

        fuzzy_predicate: TaskPredicate | None = None

        if isinstance(filter, str):
            if fuzzy:
                fuzzy_predicate = FuzzyTaskPredicate(filter)
            filter = TaskNameFilter(task_name=filter)

        matched: set[ZombuildTask] = set()
        matched_fuzzy: set[ZombuildTask] = set()

        for task in self._tasks:
            if filter.test(task.specifier):
                matched.add(task)
            if fuzzy_predicate is None or fuzzy_predicate.test(task.specifier):
                matched_fuzzy.add(task)

        if len(matched) > 0:
            return matched
        elif len(matched_fuzzy) > 0:
            return matched_fuzzy
        else:
            return matched

    def require_task(self, filter: str | ZombuildTask, fuzzy=False) -> ZombuildTask:
        """
        Variant of resolve_task that raises an exception if the filter does not resolve to one and
        only one task.

        Args:
            filter: name or predicate
            fuzzy: Enable fuzzy matching.

                Allows strings to match tasks whose names contain their characters in order, ignoring
                extra intervening characters. Defaults to False.

        Raises:
            ZombuildException: when no task is found
            ZombuildException: when multiple tasks are found by an ambiguous filter

        Returns:
            The single matched task.
        """

        if isinstance(filter, str):
            resolved = self.resolve_task(filter, fuzzy=fuzzy)
            if not resolved:
                raise ZombuildException(f"no such task: {filter}")
            if len(resolved) > 1:
                raise ZombuildException(f"ambiguous task selector: {filter}")
            return resolved.pop()
        else:
            return filter

    def lifecycle_task(self, name: str) -> LifecycleTask:
        """
        Retrieve a named lifecycle task instance, creating it if it does not exist.

        Lifecycle tasks do no work of their own, serving as top-level dependency tasks for
        build phases.

        Args:
            name: The name of the lifecycle task.

        Returns:
            LifecycleTask
        """

        if name in self._lifecycle:
            return self._lifecycle[name]
        task = LifecycleTask(invocation=self._invocation, name=name)
        self._lifecycle[name] = task
        self._tasks.append(task)
        return task

    def load_tasks(self):
        """
        Initialize user-specified tasks.
        """

        for task_name in self._invocation.config.tasks:
            task_config = self._invocation.config.tasks[task_name]

            if isinstance(task_config, str):
                task_config = TaskConfig(type=task_config)

            result = self._init_tasks_create(
                prototype=task_config.type,
                name=task_name,
                args=task_config.model_extra or {},
            )

            assert result is not None

    def _init_tasks_create(self, *, prototype: str, name: str, args: dict):

        [plugin_name, prototype_name] = prototype.split(".", 1)

        task = self._invocation.plugins.create_task(
            plugin_name=plugin_name,
            prototype_name=prototype_name,
            task_name=name,
            args=args,
        )

        self.register_task(task)
        return task

    def register_task[T: ZombuildTask](self, task: T) -> T:
        """
        Programatically register a task instance.

        Intended for use by plugins, allowing them to register automatically created tasks.

        Returns:
            The created task.
        """

        self._tasks.append(task)
        return task

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

    def collect_tasks(
        self, tasks: Sequence[str | ZombuildTask], fuzzy=False
    ) -> set[ZombuildTask]:
        """
        collects all named tasks and their dependencies

        Args:
            tasks: list of tasks or task names. Names will be resolved to tasks via
                :func:`~require_task`
            fuzzy: see :func:`~require_task`

        Returns:
            _description_
        """

        def resolve(name: str | ZombuildTask):
            return self.require_task(name, fuzzy=fuzzy)

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

    def solve_tasks(self, tasks: Sequence[str], fuzzy=False) -> list[ZombuildTask]:
        """
        Solves a list of task names from the command line, producing a list of those tasks and
        their dependencies in an appropriate execution order.

        Args:
            tasks: list of task names to resolve via :func:`~require_task`
            fuzzy: see :func:`~require_task`

        Raises:
            ZombuildException: if the task dependency graph is cyclic

        Returns:
            list of named tasks and their dependencies in execution order
        """

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

    def execute_tasks(self, tasks: Sequence[str]):
        """
        executes the named tasks and their dependencies

        Args:
            tasks: task names
        """

        order = self.solve_tasks(tasks, fuzzy=True)
        for task in order:
            self.execute_task(task)

    def execute_task(self, task: ZombuildTask):
        if not isinstance(task, LifecycleTask):
            self._invocation.console.print(
                Text("running task:", Theme.HEADING),
                Text(task.specifier.name, Theme.KEYWORD),
            )
        task.execute()


class Invocation(Tasks, InvocationBase, FeatureAccessors):
    """
    Represents an invocation of the build tool.
    """

    def __init__(
        self, arguments: ZombuildArguments, project: Path | PackageConfig
    ) -> None:
        try:
            project = resolve_package(project)
            self._project_dir = project.source.parent
            self._arguments = arguments
            self._console = Console()
            self._config = project
            self._loader = InvocationPlugins(self)
            Tasks.__init__(self, self)
        except Exception as e:
            unhandled_exception_reporter(e)

    @property
    def arguments(self) -> ZombuildArguments:
        return self._arguments

    @property
    def console(self):
        return self._console

    @property
    def plugins(self) -> InvocationPlugins:
        return self._loader

    @property
    @override
    def features(self):
        return self.plugins.features

    @property
    def config(self):
        return self._config

    @property
    def project_dir(self):
        return self._project_dir

    def execute_setup(self):
        self.plugins.load_plugins()
        self.plugins.setup_plugins()
        self.load_tasks()
        execute_setup(self._tasks, self)

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
            for plugin in self.plugins.plugins:
                for factory in plugin.tasks:
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
