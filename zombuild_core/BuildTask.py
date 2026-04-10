from typing import Sequence

from zombuild import Invocation
from zombuild.config._include import (
    Include,
    PathOrInclude,
    normalize_include,
    normalize_includes,
)
from zombuild.config._types import ItemOrSequence
from zombuild.config.definitions import ignore_default
from ._modinfo import generate_modinfo

from pathlib import Path, PurePath
from zombuild.tasks import FilesTask

# from zombuild._plan import Planner


class BuildTask(FilesTask):
    def __init__(
        self,
        *,
        invocation: Invocation,
        name: str,
        noemit: bool = False,
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
        self.noemit = noemit

        invocation.lifecycle_task("build").depends_on(self)

    def plan(self):

        self.touch(".zombuilt")
        self.file("assets/preview.png", "preview.png")
        for mod_id in self._invocation.config.mods:
            self._plan_mod(
                mod_id=mod_id,
            )

    def _include(self, includes: Sequence[Include], dst: str | PurePath):
        for include in includes:
            self.glob(
                src=include.source,
                dst=PurePath(dst) / include.prefix,
                glob="**/*",
                ignore=ignore_default(),
            )

    def _plan_mod(self, mod_id: str) -> None:
        mod = self.config.mods[mod_id]

        self.touch(
            f"Contents/mods/{mod_id}/common/.nodelete",
        )

        if (common := mod.versions.get("common")) is not None:

            self._include(
                includes=normalize_includes(common),
                dst=f"Contents/mods/{mod_id}/common",
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

            self.file(
                src=lambda dst: dst.write_text(generate_modinfo(self.config, mod_id)),
                dst=f"Contents/mods/{mod_id}/{version}/mod.info",
            )

            version_path = mod.versions[version]

            self._include(
                includes=normalize_includes(version_path),
                dst=f"Contents/mods/{mod_id}/{version}",
            )

    def execute(self) -> None:
        self.plan()
        if self.arguments.symlink:
            self._mode = "link"
        return super().execute()
