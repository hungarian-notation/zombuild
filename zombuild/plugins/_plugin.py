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

import importlib.util
import inspect
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import TYPE_CHECKING
from typing import Any
from typing import override

from zombuild._exception import ZombuildException
from zombuild.features import Feature
from zombuild.features import FeatureAccessors
from zombuild.features import Features

from ._decorator import _PLUGIN_ATTR
from ._decorator import PluginFactory
from .features import PluginOptionsFeature
from .features import TaskFeature

if TYPE_CHECKING:
    from zombuild.tasks._task import ZombuildTask


class ZombuildPlugin(FeatureAccessors, Features):
    """
    Base class implemented by all plugins.

    A plugin is chiefly a collection of PluginAttributes that describe what
    """

    def __init__(self, *, id: str | None = None, **kwargs) -> None:
        self._features: list[Feature] = []

        if id is None:
            module = inspect.getmodule(self.__class__)
            package = module.__package__ if module else None
            if package is not None:
                id = package
                if id.startswith("zombuild_"):
                    id = id.removeprefix("zombuild_")

        if id is None:
            raise ZombuildException(f"could not infer plugin id: {self}")

        self._id = id

        if kwargs:
            self.add_feature(PluginOptionsFeature(self, kwargs))

    @property
    @override
    def features(self):
        return self._features

    @property
    def id(self):
        return self._id

    @property
    def options(self) -> dict[str, Any]:
        attr = self.get_feature(PluginOptionsFeature)
        if attr:
            return attr.options
        else:
            return {}

    @property
    def tasks(self):
        tasks: dict[str, type[ZombuildTask]] = {}
        for attr in self.get_features(TaskFeature):
            tasks[attr.alias] = attr.task
        return tasks

    def add_feature(self, attr: Feature, /):
        self.features.append(attr)

    # def where(self, predicate: Callable[[PluginAttribute], bool]):
    #     return [attr for attr in self.attributes if predicate(attr)]

    def register_task(self, factory: type[ZombuildTask], *, alias: str | None = None):
        """
        Registers a task type that can be instantiated by the user via the package.tasks
        json object.

        Args:
            factory: The task's type.
                Its constructor will be invoked with the arguments provided by the user.
            alias: The task's type name at runtime.
                If `None`, the name of the task type will be used.
                Defaults to `None`.
        """
        self.add_feature(TaskFeature(self, factory, alias))

    @classmethod
    def load(cls, package_name: str, /) -> PluginFactory:

        if package_name.startswith("zombuild_"):
            search = [package_name]
        else:
            search = [package_name, f"zombuild_{package_name}"]

        package: ModuleType | None = None

        for candidate in search:
            spec: ModuleSpec | None = importlib.util.find_spec(candidate)
            if spec is not None:
                package = importlib.import_module(spec.name)
                for membername in dir(package):
                    member = getattr(package, membername)
                    if hasattr(member, _PLUGIN_ATTR):
                        return member
        else:
            if package is None:
                raise Exception(f"no such package {package_name}")
            else:
                name = package.__name__
                raise Exception(f"package {name} does not define a plugin")
