from typing import TYPE_CHECKING, Callable

from zombuild.plugins._plugin import ZombuildPlugin
from zombuild.plugins.features import PluginFeature

if TYPE_CHECKING:
    from zombuild.config.include import BuildConfig
    from zombuild_core import BuildTask
    from pathlib import PurePath


class ActionProviderFeature(PluginFeature):
    def __init__(
        self,
        plugin: ZombuildPlugin,
        name: str,
        action: Callable[[BuildTask, BuildConfig, PurePath]],
    ) -> None:
        super().__init__(plugin)
        self.name = name
        self.action = action
