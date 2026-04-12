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

from typing import Literal

from pydantic import BaseModel
from pydantic import Field

from zombuild.config.externalstring import ExternalString

VERSION = r"^[0-9]+(\.[0-9]+){1,2}$"


class PackageInfoConfig(BaseModel):
    """
    Properties used to build mod.info that are possibly common to the entire
    package.
    """

    authors: list[str] = Field(default_factory=list, description="mod.info authors")
    url: str | None = Field(default=None, description="mod.info url")
    description: str | ExternalString = Field(
        frozen=True,
        default="",
        description="mod.info description",
    )
    category: Literal["map", "vehicle", "features", "modpack"] | None = None
    versionMin: str | None = Field(default=None, pattern=VERSION)
    versionMax: str | None = Field(default=None, pattern=VERSION)

    require: list[str] = Field(default_factory=list)
    incompatible: list[str] = Field(default_factory=list)


class ModInfoConfig(PackageInfoConfig):
    """
    Properties used to build mod.info
    """

    # id: str
    name: str | None = None
    poster: str

    modversion: str | None = None
    """defaults to required version from package"""

    icon: str | None = None
    """will use the poster if not specified"""

    loadModAfter: list[str] = Field(default_factory=list)
    loadModBefore: list[str] = Field(default_factory=list)

    pack: str | list[str] = Field(default_factory=list)
    tiledef: str | list[str] = Field(default_factory=list)
