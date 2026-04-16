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

from zombuild.composite.component import Composite
from zombuild.composite.component import MutableComponents
from zombuild.composite.component_accessors import ComponentAccessorsMixin
from zombuild.composite.component_property import component_filter

from .features import PluginFeature
from .features import PluginOptionsFeature
from .features import TaskFeature

if TYPE_CHECKING:
    from zombuild.tasks._task import ZombuildTask


class ZombuildPlugin(ComponentAccessorsMixin, Composite):
    """
    Base class implemented by all plugins.

    A plugin is chiefly a collection of PluginAttributes that describe what
    """

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.id: str = getattr(type(self), "_plugin_id")
        if kwargs:
            self.add(PluginOptionsFeature(self, kwargs))

    features = component_filter(PluginFeature)

    components = MutableComponents()
    add = components.mutator()

    @property
    def options(self) -> dict[str, Any]:
        attr = self.get(PluginOptionsFeature)
        if attr:
            return attr.options
        else:
            return {}

    @property
    def tasks(self):
        tasks: dict[str, type[ZombuildTask]] = {}
        for attr in self.where(TaskFeature):
            tasks[attr.alias] = attr.task
        return tasks

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
        self.add(TaskFeature(factory, alias))
