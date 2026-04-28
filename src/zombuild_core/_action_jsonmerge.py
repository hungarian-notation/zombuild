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
from pathlib import Path
from typing import Any
from typing import Callable

from zombuild._exception import ZombuildException
from zombuild.config.include import BuildConfig
from zombuild.config.include import IncludeConfig
from zombuild_core.BuildTask import BuildTask

type JsonTransformer = Callable[[dict[str, Any]], dict[str, Any]]


def generate_output(
    inputs: list[Path], output: Path, transformer: JsonTransformer | None = None
):
    sink = dict()

    def merge(content: dict):
        for key in content:
            if key in sink:
                if sink[key] == content[key]:
                    continue
                ex = ZombuildException(
                    f"multiple json sources provide key {key}, "
                    f"but the values are not the same"
                )
                ex.add_note(f"key: {key}")
                ex.add_note(f"value #1: {sink[key]}")
                ex.add_note(f"value #2: {content[key]}")
            else:
                sink[key] = content[key]

    for input in inputs:
        with open(input, "r") as fd:
            content = json.load(fd)

            if not isinstance(content, dict):
                ex = ZombuildException(
                    "json-merge expects inputs to evaultate to a dict"
                )
                ex.add_note(f"input: {input}")
                raise ex

            if transformer:
                content = transformer(content)

            merge(content)

    with open(output, "w") as fd:
        json.dump(sink, fd, indent=2)


def json_merge_emit(
    task: BuildTask,
    output: Path,
    sources: list[Path],
    transformer: JsonTransformer | None = None,
):
    task.plan.file(lambda _: generate_output(sources, output, transformer), output)


def _merge_action(
    task: BuildTask,
    config: BuildConfig,
    prefix: Path,
    *,
    transformer: JsonTransformer | None = None,
):
    outputs: dict[Path, list[Path]] = {}

    for include in IncludeConfig.convert_list(config.target):
        collected = task.plan.collect(
            src=include.source,
            glob="**/*",
            ignore=include.ignore,
            allow_magic=True,
        )

        for item in collected:
            src = item.abs
            dst = prefix / include.prefix / item.rel
            assert dst.is_absolute()
            if dst in outputs:
                outputs[dst].append(src)
            else:
                outputs[dst] = [src]

    if not outputs:
        raise ZombuildException(f"no outputs for: {config}")

    for output in outputs:
        json_merge_emit(task, output, outputs[output], transformer)


def jsonmerge_action(
    task: BuildTask,
    config: BuildConfig,
    prefix: Path,
):
    _merge_action(task, config, prefix)
