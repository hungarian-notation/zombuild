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

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Protocol

from zombuild.plugins._plugin import ZombuildPlugin
from zombuild.plugins.features import PluginFeature

if TYPE_CHECKING:

    from zombuild.config.include import BuildConfig
    from zombuild_core import BuildTask


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
