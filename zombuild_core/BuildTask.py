import json
from os import path
from typing import Any, Sequence, TypeGuard

from zombuild import Invocation
from zombuild._exception import ZombuildException
from zombuild.config.include import (
    BuildConfig,
    IncludeConfig,
)
from zombuild_core.action_provider import ActionProviderFeature
from ._modinfo import generate_modinfo

from pathlib import Path, PurePath
from zombuild.tasks import FilesTask


def match_actionfeature(name: str):
    def predicate(feature: Any) -> TypeGuard[ActionProviderFeature]:
        if isinstance(feature, ActionProviderFeature):
            return feature.name == name
        return False

    return predicate


def default_action(task: BuildTask, build: BuildConfig, prefix: PurePath):
    for include in IncludeConfig.convert_list(build.target):
        task.glob(
            src=include.source,
            dst=prefix / include.prefix,
            glob="**/*",
            ignore=[],
        )


def generate_output(inputs: list[Path], output: Path):
    print(f"generate_output({output})")
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
            merge(content)

    with open(output, "w") as fd:
        json.dump(sink, fd)


def json_merge_emit(task: BuildTask, output: Path, sources: list[Path]):
    print(f"output: {output}")
    task.file(lambda _: generate_output(sources, output), output)


def json_merge_action(task: BuildTask, build: BuildConfig, prefix: PurePath):
    outputs: dict[str, list[Path]] = {}

    for include in IncludeConfig.convert_list(build.target):
        collected = task.collect(
            src=include.source,
            dst=prefix / include.prefix,
            glob="**/*",
            ignore=[],
        )

        for item in collected:
            src, dst = item["src"], item["dst"]
            if dst in outputs:
                outputs[str(dst)].append(src)
            else:
                outputs[str(dst)] = [src]

    for output in outputs:
        json_merge_emit(task, Path(output), outputs[output])


class BuildTask(FilesTask):
    def __init__(
        self,
        *,
        invocation: Invocation,
        name: str,
        output_path: Path,
        **extra,
    ) -> None:
        super().__init__(
            invocation=invocation,
            name=name,
            srcroot=invocation.project_dir,
            dstroot=Path(output_path).expanduser().resolve(),
        )

        self.target = Path(output_path).expanduser().resolve()

        invocation.lifecycle_task("build").depends_on(self)

    def _actions(self, action_config: Sequence[BuildConfig], output_base: PurePath):
        for include in action_config:
            action = include.action
            provider = self.invocation.get_feature(match_actionfeature(action))
            if provider is None:
                raise ZombuildException(
                    f"no build action provider for action: {action}"
                )
            provider.action(self, include, output_base)

    def package(self):
        self.touch(".zombuilt")
        self.file("assets/preview.png", "preview.png")
        for mod_id in self._invocation.config.mods:
            self.mod(
                mod_id=mod_id,
            )

    def mod(self, mod_id: str) -> None:
        mod = self.config.mods[mod_id]
        self.touch(
            f"Contents/mods/{mod_id}/common/.nodelete",
        )

        poster_path = Path(mod.poster)
        icon_path: Path | None = None

        if mod.icon is not None:
            icon_path = Path(mod.icon)

        self.file(
            src=poster_path,
            dst=f"Contents/mods/{mod_id}/common/{poster_path.name}",
        )

        if icon_path is not None:
            self.file(
                src=icon_path,
                dst=f"Contents/mods/{mod_id}/common/{icon_path.name}",
            )

        for version in mod.versions:
            if version != "common":
                self.file(
                    src=lambda dst: dst.write_text(
                        generate_modinfo(self.config, mod_id)
                    ),
                    dst=f"Contents/mods/{mod_id}/{version}/mod.info",
                )

            version_path = mod.versions[version]

            self._actions(
                action_config=BuildConfig.convert_list(version_path),
                output_base=PurePath(f"Contents/mods/{mod_id}/{version}"),
            )

    def execute(self) -> None:
        self.package()
        if self.arguments.symlink:
            self._mode = "link"
        return super().execute()
