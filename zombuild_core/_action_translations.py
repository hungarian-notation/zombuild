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

from zombuild._exception import ZombuildException
from zombuild.config.include import BuildConfig
from zombuild_core._action_jsonmerge import _merge_action
from zombuild_core.BuildTask import BuildTask


def transform_translation(content: dict[str, Any]):
    results: list[tuple[str, str]] = []

    def name(*parts: str):
        segments: list[str] = []
        for part in parts:
            if part == "@":
                continue
            if part.startswith("."):
                segments.append(part[1:])
                continue
            if segments:
                segments.append("_")
            segments.append(part)
        return "".join(segments)

    def visit(object: dict[str, Any], context: list[str]):
        for k, v in object.items():
            if isinstance(v, str):
                results.append((name(*context, k), v))
            elif isinstance(v, dict):
                visit(v, [*context, k])
            elif isinstance(v, list):
                for item in v:
                    if not isinstance(item, str):
                        raise ZombuildException(
                            f"unexpected value of type {str(type(item))} in {name(*context,k)}"
                        )
                results.append((name(*context, k), " ".join(v)))
            else:
                raise ZombuildException(
                    f"unexpected value of type {str(type(v))} in {name(*context,k)}"
                )

    visit(content, [])

    transformed: dict[str, str] = dict()

    for result in results:
        key, value = result
        transformed[key] = value

    return transformed


def translations_action(
    task: BuildTask,
    config: BuildConfig,
    prefix: Path,
):
    _merge_action(task, config, prefix, transformer=transform_translation)
