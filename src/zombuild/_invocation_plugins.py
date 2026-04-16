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

from importlib.metadata import entry_points
from typing import TYPE_CHECKING
from typing import Iterable

from zombuild._context import context_config
from zombuild._exception import ZombuildException
from zombuild.composite.hooks import execute_hook
from zombuild.config.package import PackageConfig
from zombuild.config.plugin import PluginConfig
from zombuild.plugins import ZombuildPlugin
from zombuild.setup_hook import SetupHook

if TYPE_CHECKING:
    pass


def find_plugin(name):
    for plugin in entry_points(group="zombuild_plugins"):
        if plugin.name == name:
            loaded = plugin.load()
            if isinstance(loaded, type) and issubclass(loaded, ZombuildPlugin):
                setattr(loaded, "_plugin_id", name)
                return loaded
            else:
                raise Exception(
                    f"expected plugin entry point {plugin} "
                    f"to refer to a subclass of ZombuildPlugin"
                )
    else:
        raise Exception(f"no such plugin: {name}")


class Plugins:
    def __init__(self) -> None:
        self._plugins: dict[str, ZombuildPlugin] = dict()

    @property
    def plugins(self) -> Iterable[ZombuildPlugin]:
        return self._plugins.values()

    def load(self, *, package: PackageConfig | None = None, skip_setup=False):
        package = package or context_config()
        for plugin in package.plugins:
            config = PluginConfig.convert(plugin)
            factory = find_plugin(config.plugin)
            plugin = factory(**(config.model_extra or {}))
            self._plugins[plugin.id] = plugin

        if not skip_setup:
            self.setup()

    def setup(self):
        execute_hook(SetupHook, self.plugins)

    def plugin(self, name: str):
        plugin = self._plugins.get(name)
        if plugin is None:
            raise ZombuildException(f"no such plugin: {name}")
        return plugin


# class InvocationPlugins(ComponentAccessorsMixin):
#     def __init__(self, invocation: Invocation) -> None:
#         self._plugins: dict[str, ZombuildPlugin] = dict()
#         self._invocation = invocation

#     @property
#     def package(self):
#         return self._invocation.config

#     @property
#     def plugins(self) -> Iterable[ZombuildPlugin]:
#         return self._plugins.values()

#     @property
#     @override
#     def components(self):
#         return components(self.plugins)

#     def load_plugins(self):
#         for plugin in self.package.plugins:
#             config = PluginConfig.convert(plugin)

#             factory = find_plugin(config.plugin)
#             plugin = factory(
#                 invocation=self._invocation,
#                 **(config.model_extra or {}),
#             )
#             self._plugins[plugin.id] = plugin

#     def setup_plugins(self):
#         execute_hook(SetupHook, self.plugins)

#     def plugin(self, name: str):
#         plugin = self._plugins.get(name)
#         if plugin is None:
#             raise ZombuildException(f"no such plugin: {name}")
#         return plugin

#     def plugin_where(self, condition: Callable[[ZombuildPlugin], bool]):
#         return [matched for matched in self.plugins if condition(matched)]

#     def plugin_with(self, condition):
#         return (plugin for plugin in self.plugins if plugin.has(condition))
