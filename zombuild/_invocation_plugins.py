from typing import TYPE_CHECKING

from zombuild._exception import ZombuildException
from zombuild.config import PluginConfig
from zombuild.plugins import ZombuildPlugin
from zombuild.tasks import ZombuildTask

if TYPE_CHECKING:
    from ._invocation import Invocation


class InvocationPlugins:
    def __init__(self, invocation: Invocation) -> None:
        self._plugins: dict[str, ZombuildPlugin] = dict()
        self._invocation = invocation

    @property
    def package(self):
        return self._invocation.config

    def init_plugins(self):
        for plugin in self.package.plugins:
            cfg = PluginConfig.convert(plugin)
            self.register_plugin(cfg)

    def setup_plugins(self):
        for plugin in self.plugins:
            plugin.setup(self._invocation)

    def register_plugin(self, config: PluginConfig):
        factory = ZombuildPlugin.load(config.plugin)

        plugin = factory(
            invocation=self._invocation,
            **(config.model_extra or {}),
        )

        self._plugins[plugin.id] = plugin

    @property
    def plugins(self):
        return self._plugins.values()

    def plugin(self, name: str):
        plugin = self._plugins.get(name)
        if plugin is None:
            raise ZombuildException(f"no such plugin: {name}")
        return plugin
    
    def create_task(
        self,
        plugin_name: str,
        prototype_name: str,
        task_name: str,
        args: dict,
    ) -> ZombuildTask:

        plugin = self.plugin(plugin_name)
        factory = plugin.task_prototypes[prototype_name]

        args = dict(**plugin.options, **args)
        args["invocation"] = self._invocation
        args["name"] = task_name

        task = factory(**args)

        return task
