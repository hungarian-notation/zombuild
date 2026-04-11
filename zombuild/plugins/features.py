from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Final,
    Protocol,
    override,
    runtime_checkable,
)

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
