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
import json
import urllib.parse
from pathlib import Path

from pydantic import ValidationError

from .config.package import PackageConfig
from zombuild._exception import ZombuildConfigException
from zombuild._exception import ZombuildException
from zombuild._schema import write_schema


def is_uri_with_schema(string):
    parsed = urllib.parse.urlparse(string)
    return parsed.scheme is not None and parsed.scheme != ""


def resolve_package(project: Path | PackageConfig) -> PackageConfig:
    if isinstance(project, PackageConfig):
        return project

    search_path = [project / "zombuild.json", project / "zombmod.json"]

    if project.is_dir():
        for path in search_path:
            if path.is_file():
                project = path

    if not project.is_file():
        e = ZombuildException(f"missing zombuild.json at project root")
        for path in search_path:
            e.add_note(f"tried: {path}")
        raise e

    package_json = json.loads(project.read_text())

    try:
        package = PackageConfig(**package_json, source=project)
    except ValidationError as e:
        raise ZombuildConfigException(validation_error=e)

    schema = package.schema_reference

    if schema is not None and not is_uri_with_schema(schema):
        schema_path = Path(schema).resolve()
        if schema_path.is_relative_to(project.parent):
            write_schema(schema_path)

    return package
