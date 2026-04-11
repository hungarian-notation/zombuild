from typing import TYPE_CHECKING, Callable, override

from zombuild import plugins
from zombuild._exception import ZombuildException
from zombuild.config import PluginConfig
from zombuild.lifecycle_mixins import execute_setup
from zombuild.plugins._plugin import FeatureAccessors
from zombuild.plugins.features import PluginFeature
from zombuild.tasks import ZombuildTask
from zombuild.plugins import ZombuildPlugin

if TYPE_CHECKING:
    from ._invocation import Invocation


class InvocationPlugins(FeatureAccessors):
    def __init__(self, invocation: Invocation) -> None:
        self._plugins: dict[str, ZombuildPlugin] = dict()
        self._invocation = invocation

    @property
    def package(self):
        return self._invocation.config

    @property
    def plugins(self):
        return self._plugins.values()

    @property
    @override
    def features(self):
        return [feature for plugin in self.plugins for feature in plugin.features]

    def load_plugins(self):
        for plugin in self.package.plugins:
            config = PluginConfig.convert(plugin)
            factory = ZombuildPlugin.load(config.plugin)
            plugin = factory(
                invocation=self._invocation,
                **(config.model_extra or {}),
            )
            self._plugins[plugin.id] = plugin

    def setup_plugins(self):
        features = [feature for plugin in self.plugins for feature in plugin.features]
        execute_setup(features, self._invocation)

    def plugin(self, name: str):
        plugin = self._plugins.get(name)
        if plugin is None:
            raise ZombuildException(f"no such plugin: {name}")
        return plugin

    def where(self, condition: Callable[[ZombuildPlugin], bool]):
        return [matched for matched in self.plugins if condition(matched)]

    def with_feature(
        self, condition: type[PluginFeature] | Callable[[PluginFeature], bool]
    ):
        return self.where(lambda plugin: plugin.has_feature(condition))

    def create_task(
        self,
        plugin_name: str,
        prototype_name: str,
        task_name: str,
        args: dict,
    ) -> ZombuildTask:

        plugin = self.plugin(plugin_name)
        factory = plugin.tasks.get(prototype_name)

        if factory is None:
            raise ZombuildException(f"no such task: {plugin_name}.{prototype_name}")

        args = dict(**plugin.options, **args)
        args["invocation"] = self._invocation
        args["name"] = task_name

        task = factory(**args)

        return task
