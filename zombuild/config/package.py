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
from typing import Any
from typing import Literal

from pydantic import ConfigDict
from pydantic import Field

from zombuild.config.include import BuildActionLike
from zombuild.config.modinfo import ModInfoConfig
from zombuild.config.modinfo import PackageInfoConfig
from zombuild.config.plugin import PluginConfig
from zombuild.config.task import TaskConfig
from zombuild.config.withpath import WithPath


class ModConfig(ModInfoConfig, WithPath):
    model_config = ConfigDict(extra="allow")
    versions: dict[str | Literal["common"], BuildActionLike | list[BuildActionLike]]


class PackageConfig(PackageInfoConfig, WithPath):
    model_config = ConfigDict(extra="ignore")

    schema_reference: str | None = Field(default=None, alias="$schema")
    "schema path/uri"

    id: str
    name: str
    version: str
    preview: str
    mods: dict[str, ModConfig] = Field(min_length=1)

    plugins: list[str | PluginConfig] = Field(
        default_factory=list, examples=[["core"], [{"plugin": "core", "args": {}}]]
    )
    tasks: dict[str, str | TaskConfig] = Field(
        default_factory=dict,
        examples=[
            {
                "build": "core.build",
                "clean": "core.clean",
                "clean-build": ["clean", "build"],
            }
        ],
    )

    output: str | Path = Field(
        description="output path (used by core plugin)", default="dist"
    )

    def __init__(self, **kwds: Any) -> None:
        super().__init__(**kwds)

        if "source" in kwds:
            self.source = kwds["source"]
            for mod in self.mods.values():
                mod.source = self.source
