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
from typing import Any
from typing import Callable
from typing import Final
from typing import override
from typing import Protocol
from typing import runtime_checkable
from typing import TYPE_CHECKING

from zombuild.lifecycle_mixins import WithSetupLifecycle

if TYPE_CHECKING:
    from zombuild.tasks._task import ZombuildTask
    from zombuild._invocation import Invocation
    from ._plugin import ZombuildPlugin


class PluginFeature(ABC, WithSetupLifecycle["Invocation"]):
    def __init__(self, plugin: ZombuildPlugin) -> None:
        super().__init__()
        self.plugin: Final[ZombuildPlugin] = plugin


class OptionsFeature(PluginFeature):
    def __init__(self, plugin: ZombuildPlugin, options: dict[str, Any]) -> None:
        super().__init__(plugin=plugin)
        self.options = options


class TaskFeature(PluginFeature):
    def __init__(
        self,
        plugin: ZombuildPlugin,
        task_type: type[ZombuildTask],
        task_alias: str | None = None,
    ) -> None:
        super().__init__(plugin=plugin)
        self.task = task_type
        self.alias = task_alias if task_alias else task_type.__name__


@dataclass
class DefaultTaskFeature(PluginFeature):
    create_tasks: Callable[[Invocation], None]
    wire_tasks: Callable[[Invocation], None] | None = None

    @override
    def setup(self, invocation: Invocation):
        self.create_tasks(invocation)

    @override
    def setup_late(self, invocation: Invocation):
        if self.wire_tasks:
            self.wire_tasks(invocation)


# class DefaultTaskFactory[T: ZombuildTask](Protocol):
#     def __call__(self, invocation: Invocation, **kwargs: Any) -> T: ...


# class DefaultTaskAttribute[T: ZombuildTask](PluginAttribute):
#     def __init__(
#         self,
#         plugin: ZombuildPlugin,
#         factory: DefaultTaskFactory[T],
#         *,
#         factory_kwargs: dict | None = None,
#     ) -> None:
#         super().__init__(plugin=plugin)
#         self.factory = factory
#         self.factory_kwargs = factory_kwargs or {}

#     def resolve(self, invocation: Invocation):
#         return self.factory(invocation=invocation, **self.factory_kwargs)
