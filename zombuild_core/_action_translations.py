from zombuild._exception import ZombuildException
from typing import Any

from zombuild.config.include import BuildConfig
from zombuild_core.BuildTask import BuildTask
from zombuild_core._action_jsonmerge import _merge_action
from pathlib import Path

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