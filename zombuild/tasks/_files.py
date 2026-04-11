import os
from typing import TYPE_CHECKING, Any, Callable, Literal, TypedDict, overload
import warnings


from zombuild.fs import Plan
from zombuild.tasks._default import ActionableTask
from dataclasses import dataclass
from pathlib import Path, PurePath

if TYPE_CHECKING:
    from zombuild import Invocation


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

    The `touch(...)` `file(...)` and `glob(...)` methods can be used by subclasses to describe the
    desired operations.
    """

    def __init__(
        self,
        *,
        invocation: Invocation,
        name: str,
        mode: Literal["copy", "link"] = "copy",
        srcroot: Path,
        dstroot: Path,
    ) -> None:
        super().__init__(
            name=name,
            invocation=invocation,
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
            perform_operations=not self.invocation.arguments.dry_run,
        )
