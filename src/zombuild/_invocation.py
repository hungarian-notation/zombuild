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

from dataclasses import replace
from importlib.metadata import entry_points
from pathlib import Path
from typing import Sequence
from warnings import deprecated

from zombuild._context import ZombuildContext
from zombuild._context import context
from zombuild.composite.component import Component
from zombuild.composite.component import DerivedComponents
from zombuild.composite.component_accessors import ComponentAccessorsMixin
from zombuild.composite.hooks import execute_hook
from zombuild.setup_hook import SetupHook

from ._arguments import ZombuildArguments
from ._create_task import create_task
from ._exception import ZombuildException
from ._exception import unhandled_exception_reporter
from ._invocation_base import InvocationBase
from ._invocation_plugins import Plugins
from ._package import resolve_package
from .config.task import TaskConfig
from .console import Console
from .console import Indent
from .console import Text
from .tasks import ZombuildTask
from .tasks._default import ActionableTask
from .tasks._default import LifecycleTask
from .theme import Theme


class Tasks:
    def __init__(self, invocation: Invocation) -> None:
        self._tasks: list[ZombuildTask] = []
        self._lifecycle: dict[str, LifecycleTask] = dict()
        self._invocation = invocation

    @property
    def tasks(self):
        return self._tasks

    def resolve_task(self, name: str) -> set[ZombuildTask]:
        return set(each for each in self._tasks if each.name == name)

    def require_task(self, filter: str | ZombuildTask) -> ZombuildTask:
        """
        Variant of resolve_task that raises an exception if the filter does not resolve
        to one and only one task.

        Args:
            filter: name or predicate

        Raises:
            ZombuildException: when no task is found
            ZombuildException: when multiple tasks are found by an ambiguous filter

        Returns:
            The single matched task.
        """

        if isinstance(filter, str):
            resolved = self.resolve_task(filter)
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

        Lifecycle tasks do no work of their own, serving as top-level dependency tasks
        for build phases.

        Args:
            name: The name of the lifecycle task.

        Returns:
            LifecycleTask
        """

        if name in self._lifecycle:
            return self._lifecycle[name]
        task = LifecycleTask(name=name)
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

        task = create_task(
            self._invocation.plugins,
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

        Intended for use by plugins, allowing them to register automatically created
        tasks.

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

    def collect_tasks(self, tasks: Sequence[str | ZombuildTask]) -> set[ZombuildTask]:
        """
        collects all named tasks and their dependencies

        Args:
            tasks: list of tasks or task names. Names will be resolved to tasks via
                :func:`~require_task`

        Returns:
            _description_
        """

        def resolve(name: str | ZombuildTask):
            return self.require_task(name)

        queue = set(map(resolve, tasks))
        seen = set(queue)

        while len(queue) > 0:
            task = queue.pop()
            required = task.get_dependencies(self.tasks, include_optional=False)

            for other in required:
                if other not in seen:
                    queue.add(other)
                    seen.add(other)
        return seen

    def solve_tasks(self, tasks: Sequence[str]) -> list[ZombuildTask]:
        """
        Solves a list of task names from the command line, producing a list of those
        tasks and their dependencies in an appropriate execution order.

        Args:
            tasks: list of task names to resolve via :func:`~require_task`

        Raises:
            ZombuildException: if the task dependency graph is cyclic

        Returns:
            list of named tasks and their dependencies in execution order
        """

        unsorted = list(self.collect_tasks(tasks))
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

        order = self.solve_tasks(tasks)
        for task in order:
            self.execute_task(task)

    def execute_task(self, task: ZombuildTask):
        if not isinstance(task, LifecycleTask):
            print(
                Text("running task:", Theme.HEADING),
                Text(task.name, Theme.KEYWORD),
            )
        task.execute()


class Invocation(Tasks, InvocationBase, ComponentAccessorsMixin):
    """
    Represents an invocation of the build tool.
    """

    def __init__(self, arguments: ZombuildArguments, project: Path) -> None:

        nascent_context = ZombuildContext(
            invocation=self,
            arguments=arguments,
            project=project,
            features=self,
        )

        context.set(nascent_context)

        try:
            self._config = resolve_package(project)
            context.set(replace(nascent_context, config=self._config))

            self._project_dir = self._config.source.parent
            self._arguments = arguments
            self._console = Console()
            self._loader = Plugins()
            Tasks.__init__(self, self)
        except Exception as e:
            unhandled_exception_reporter(e)

    def __derive(self):
        v: set[Component] = set()
        v |= set(x for p in self.plugins.plugins for x in p.components)
        v |= set(x for p in self.tasks for x in p.components)
        return v

    components = DerivedComponents(__derive)

    @property
    @deprecated("use context module")
    def arguments(self) -> ZombuildArguments:
        return self._arguments

    @property
    @deprecated("use context module")
    def console(self):
        return self._console

    @property
    def plugins(self) -> Plugins:
        return self._loader

    @property
    def config(self):
        return self._config

    @property
    def project_dir(self):
        return self._project_dir

    def execute_setup(self):
        self.plugins.load()
        self.load_tasks()
        execute_hook(SetupHook, self._tasks)

    def execute_run(self):
        self.execute_tasks(self.arguments.tasks)  # type: ignore

    def execute_list(self):

        print()
        print(Text("Supertasks:", Theme.HEADING))

        for task in self._tasks:
            if isinstance(task, LifecycleTask):
                txt_name = Text(task.name, Theme.KEYWORD)

                print(
                    Indent(
                        txt_name,
                        2,
                    )
                )

        print()
        print(Text("Tasks:", Theme.HEADING))

        for task in self._tasks:
            if isinstance(task, ActionableTask):
                txt_name = Text(task.name, Theme.KEYWORD)

                print(
                    Indent(
                        txt_name,
                        2,
                    )
                )

        if self._arguments.list_types:
            print()
            print(Text("Task Types:", Theme.HEADING))
            for plugin in self.plugins.plugins:
                for factory in plugin.tasks:
                    t = Text()
                    t.append(plugin.id)
                    t.append(".")
                    t.append(factory)
                    print(Indent(t, 2))

        if self._arguments.list_plugins:
            print()
            print(Text("Available Plugins:", Theme.HEADING))
            for plugin in entry_points(group="zombuild_plugins"):
                t = Text()
                t.append(plugin.name)
                if plugin.dist is not None:
                    t.append(f" (from {plugin.dist.name})")
                print(Indent(t, 2))

    def execute(self):
        try:
            command = self._arguments.command

            self.execute_setup()

            if command == "list":
                self.execute_list()
            elif command == "run":
                self.execute_run()
            elif command in ("", None):
                raise ZombuildException("missing command; try: `zombuild list`")
            else:
                raise ZombuildException(f'unknown command: "{command}"')
        except Exception as e:
            unhandled_exception_reporter(e)
