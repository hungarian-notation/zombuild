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

from typing import TYPE_CHECKING
from typing import Any
from typing import override

from zombuild.features import Feature
from zombuild.features import FeatureAccessors
from zombuild.features import Features

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
        self._id: str | None = None
        self._group: str | None = None
        if kwargs:
            self.add_feature(PluginOptionsFeature(self, kwargs))

    @property
    @override
    def features(self):
        return self._features

    @property
    def id(self):
        if self._id is None:
            raise ValueError(f"id not set on {self}")
        return self._id

    @id.setter
    def id(self, id: str):
        if self._id is not None:
            raise ValueError(f"id was already set on {self}")
        self._id = id

    @property
    def group(self):
        if self._group is None:
            raise ValueError(f"group not set on {self}")
        return self._group

    @group.setter
    def group(self, group: str):
        if self._group is not None:
            raise ValueError(f"group was already set on {self}")
        self._group = group

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
