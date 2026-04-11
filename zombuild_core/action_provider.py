from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Protocol

from zombuild.plugins._plugin import ZombuildPlugin
from zombuild.plugins.features import PluginFeature

if TYPE_CHECKING:
    from zombuild.config.include import BuildConfig
    from zombuild_core import BuildTask
    from pathlib import PurePath


class BuildAction(Protocol):
    def __call__(self, task: BuildTask, config: BuildConfig, prefix: Path) -> Any: ...


class ActionProviderFeature(PluginFeature):
    def __init__(
        self,
        plugin: ZombuildPlugin,
        name: str,
        action: BuildAction,
    ) -> None:
        super().__init__(plugin)
        self.name = name
        self.action = action
