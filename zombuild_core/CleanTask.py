from pathlib import Path
import shutil
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
            path.rmdir()
        else:
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.is_dir():
                self._rm(path)
