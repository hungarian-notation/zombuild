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
from typing import Final

from zombuild.features import Feature
from zombuild.features import Features

if TYPE_CHECKING:
    from zombuild.tasks._task import ZombuildTask

    from ._plugin import ZombuildPlugin


class PluginFeature(Feature):
    def __init__(self, plugin: ZombuildPlugin) -> None:
        super().__init__(provider=plugin)
        self.plugin: Final[ZombuildPlugin] = plugin


class PluginOptionsFeature(PluginFeature):
    def __init__(self, plugin: ZombuildPlugin, options: dict[str, Any]) -> None:
        super().__init__(plugin=plugin)
        self.options = options


class TaskFeature(Feature):
    def __init__(
        self,
        provider: Features,
        task_type: type[ZombuildTask],
        task_alias: str | None = None,
    ) -> None:
        super().__init__(provider)
        self.task = task_type
        self.alias = task_alias if task_alias else task_type.__name__
