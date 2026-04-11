import glob
import json
from typing import Any, Callable

from zombuild._exception import ZombuildException
from zombuild.config.include import BuildConfig, IncludeConfig
from zombuild.tasks._files import FilesTask
from zombuild_core.BuildTask import BuildTask


from pathlib import Path, PurePath

type JsonTransformer = Callable[[dict[str, Any]], dict[str, Any]]


def generate_output(
    inputs: list[Path], output: Path, transformer: JsonTransformer | None = None
):
    sink = dict()

    def merge(content: dict):
        for key in content:
            if key in sink:
                if sink[key] != content[key]:
                    ex = ZombuildException(
                        f"multiple json sources provide key {key}, but the values are not the same"
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
                    f"json-merge expects inputs to evaultate to a dict"
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
            ignore=[],
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




