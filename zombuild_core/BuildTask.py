from os import path
from typing import Any, Sequence, TypeGuard

from zombuild import Invocation
from zombuild._exception import ZombuildException
from zombuild.config.include import (
    BuildConfig,
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

    def _actions(self, config: Sequence[BuildConfig], prefix: Path):
        for include in config:
            action = include.action
            provider = self.invocation.get_feature(match_actionfeature(action))
            if provider is None:
                raise ZombuildException(
                    f"no build action provider for action: {action}"
                )
            provider.action(self, include, prefix)

    def _package(self):
        self.plan.touch(".zombuilt")
        self.plan.file("assets/preview.png", "preview.png")
        for mod_id in self._invocation.config.mods:
            self._mod(
                mod_id=mod_id,
            )

    def _mod(self, mod_id: str) -> None:
        mod = self.config.mods[mod_id]

        self.plan.touch(f"Contents/mods/{mod_id}/common/.nodelete")

        poster_path = Path(mod.poster)
        icon_path: Path | None = None

        if mod.icon is not None:
            icon_path = Path(mod.icon)

        self.plan.file(
            src=poster_path,
            dst=f"Contents/mods/{mod_id}/common/{poster_path.name}",
        )

        if icon_path is not None:
            self.plan.file(
                src=icon_path,
                dst=f"Contents/mods/{mod_id}/common/{icon_path.name}",
            )

        for version in mod.versions:
            if version != "common":
                self.plan.file(
                    src=lambda dst: dst.write_text(
                        generate_modinfo(self.config, mod_id)
                    ),
                    dst=f"Contents/mods/{mod_id}/{version}/mod.info",
                )

            version_path = mod.versions[version]

            self._actions(
                config=BuildConfig.convert_list(version_path),
                prefix=self.plan.resolve_destination(
                    f"Contents/mods/{mod_id}/{version}"
                ),
            )

    def execute(self) -> None:
        self._package()
        if self.arguments.symlink:
            self.plan.mode = "link"
        return super().execute()
