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
from typing import Sequence
from typing import TypeGuard

from zombuild._context import context_arguments
from zombuild._context import context_config
from zombuild._context import context_invocation
from zombuild._context import context_project
from zombuild._exception import ZombuildException
from zombuild.config.include import BuildConfig
from zombuild.tasks import FilesTask
from zombuild_core.action_provider import ActionProviderFeature

from ._modinfo import generate_modinfo


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
        name: str,
        output_path: Path,
        **extra,
    ) -> None:
        super().__init__(
            name=name,
            srcroot=context_project(),
            dstroot=Path(output_path).expanduser().resolve(),
        )

        self.target = Path(output_path).expanduser().resolve()

        context_invocation().lifecycle_task("build").depends_on(self)

    def _actions(self, config: Sequence[BuildConfig], prefix: Path):
        for include in config:
            action = include.action
            provider = self.invocation.get(match_actionfeature(action))
            if provider is None:
                raise ZombuildException(
                    f"no build action provider for action: {action}"
                )
            provider.action(self, include, prefix)

    def _package(self):
        self.plan.touch(".zombuilt")
        self.plan.file("assets/preview.png", "preview.png")
        for mod_id in context_config(True).mods:
            self._mod(
                mod_id=mod_id,
            )

    def _mod(self, mod_id: str) -> None:
        mod = context_config().mods[mod_id]

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
                        generate_modinfo(context_config(), mod_id)
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
        if context_arguments().symlink:
            self.plan.mode = "link"
        return super().execute()
