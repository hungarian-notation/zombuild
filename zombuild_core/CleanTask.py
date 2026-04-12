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
import shutil
from pathlib import Path
from typing import ClassVar
from unittest.mock import sentinel

from zombuild import Invocation
from zombuild.tasks import ActionableTask


class CleanTask(ActionableTask):

    def __init__(
        self,
        invocation: Invocation,
        name: str,
        output_path: Path,
        **extra,
    ) -> None:
        super().__init__(
            invocation=invocation,
            name=name,
        )
        self.output_path = Path(output_path).expanduser().resolve()

        invocation.lifecycle_task("clean").depends_on(self)

    def execute(self) -> None:
        if self.output_path.exists():
            if self.output_path.is_dir():
                sentinel_path = self.output_path / ".zombuilt"
                if sentinel_path.exists():
                    self._rm(self.output_path)
                else:
                    raise Exception(
                        f"{self.output_path} does not appear to be a zombuild output"
                    )
            else:
                raise Exception(f"{self.output_path} is not a directory")

    def _rm(self, path: Path):
        if path.is_dir():
            for item in path.iterdir():
                self._rm(item)
            self.perform_work(
                lambda: path.rmdir(),
                "remove dir",
                path=path,
            )
        else:
            if path.is_symlink() or path.is_file():
                self.perform_work(
                    lambda: path.unlink(),
                    "unlink file or symlink",
                    path=path,
                )
            elif path.is_dir():
                self._rm(path)
