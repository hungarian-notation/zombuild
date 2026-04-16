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

import os
from pathlib import Path
from pathlib import PurePath
from typing import Literal
from typing import overload

from zombuild._context import context_arguments
from zombuild.fs import Plan
from zombuild.tasks._default import ActionableTask


@overload
def normalize(path: Path | PurePath) -> Path: ...


@overload
def normalize(path: None | Path | PurePath) -> None | Path: ...


def normalize(path: None | Path | PurePath) -> None | Path:
    if path is None:
        return None

    assert path.is_absolute()

    if (norm := os.path.normpath(path)) != str(path) or not isinstance(path, Path):
        return Path(norm)
    else:
        return path


class FilesTask(ActionableTask):
    """
    A task that enacts a set of filesystem operations.

    The `touch(...)` `file(...)` and `glob(...)` methods can be used by subclasses to
    describe the desired operations.
    """

    def __init__(
        self,
        *,
        name: str,
        mode: Literal["copy", "link"] = "copy",
        srcroot: Path,
        dstroot: Path,
    ) -> None:
        super().__init__(
            name=name,
        )

        self.mode = mode

        self.plan = Plan(
            mode=mode,
            srcroot=srcroot,
            dstroot=dstroot,
            enforce_relative="dst",
        )

    @property
    def inputs(self) -> list[Path]:
        files = []
        for item in self.plan.items:
            if isinstance(item, Path):
                files.append(item.src)
        return files

    @property
    def outputs(self) -> list[Path]:
        files = []
        for item in self.plan.items:
            files.append(item.dst)
        return files

    def resolve_source(self, src: str | PurePath):
        return self.plan.resolve_source(src)

    def resolve_destination(self, dst: str | PurePath):
        return self.plan.resolve_destination(dst)

    def execute(self) -> None:
        self.plan.execute(
            listener=lambda message, *, path, source=None: self.log_work(
                message,
                path=path,
                source=source,
            ),
            perform_operations=not context_arguments().dry_run,
        )
