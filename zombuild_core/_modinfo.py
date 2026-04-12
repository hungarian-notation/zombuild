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
import re
from pathlib import Path
from pathlib import PurePosixPath
from typing import Sequence
from typing import Tuple

from zombuild.config.externalstring import ExternalString
from zombuild.config.package import PackageConfig

type ModInfoString = str
type ModInfoStringList = Sequence[ModInfoString]
type ModInfo = list[Tuple[str, None | ModInfoString | ModInfoStringList]]


def generate_modinfo(package: PackageConfig, id: str) -> str:
    """derives the content of a mod.info file for the given package and modid

    Args:
        package (PackageDict): the package
        id (str): the mod in the package to generate a mod.info for

    Returns:
        str: the contents of the mod.info file
    """
    return _format_modinfo(_derive_modinfo(package, id))


def normalize_text(value: str, /, *, line_break: str = r" <BR> "):
    normalized = re.sub(r"(?:\s*[\r]?[\n]\s*){2,}", line_break, value)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _derive_modinfo(package: PackageConfig, id: str) -> ModInfo:
    def delistify(arr: list[str]):
        return ",".join(arr)

    assert id in package.mods, f"no such mod in package: {id}"
    mod = package.mods[id]

    info: ModInfo = []

    ## NAME
    info.append(("name", mod.name or package.name or id))

    ## ID
    info.append(("id", id))

    ## AUTHOR

    info.append(("author", [*mod.authors, *package.authors]))

    ## DESCRIPTION

    info.append(
        (
            "description",
            normalize_text(
                ExternalString.resolve(mod.description or package.description, mod)
            ),
        )
    )

    ## URL

    info.append(("url", mod.url or package.url))

    ## POSTER & ICON

    poster_path = str(PurePosixPath("..") / "common" / Path(mod.poster).name)
    icon_path = str(PurePosixPath("..") / "common" / Path(mod.icon or mod.poster).name)

    info.append(("poster", poster_path))
    info.append(("icon", icon_path))

    ## MODVERSION

    info.append(("modversion", mod.modversion or package.version))

    ## DEPENDENCIES

    info.append(("require", [*mod.require, *package.require]))
    info.append(("incompatible", [*mod.incompatible, *package.incompatible]))
    info.append(("loadModAfter", mod.loadModAfter))
    info.append(("loadModBefore", mod.loadModBefore))
    info.append(("category", mod.category or package.category))
    info.append(("pack", mod.pack))
    info.append(("tiledef", [*mod.tiledef]))
    info.append(("versionMin", mod.versionMin or package.versionMin))
    info.append(("versionMax", mod.versionMax or package.versionMax))

    return info


def _format_modinfo(modinfo: ModInfo) -> str:
    lines = []
    for entry in modinfo:
        key = entry[0]
        value = entry[1]

        if isinstance(value, str):
            value = value
        elif isinstance(value, Sequence):
            if len(value) == 0:
                value = None
            else:
                value = ",".join(value)
        if value is not None:
            lines.append(f"{key}={value}")
    return "\n".join(lines)
