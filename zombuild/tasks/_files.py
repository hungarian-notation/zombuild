from typing import TYPE_CHECKING, Callable, Literal


from zombuild._exception import ZombuildException
from zombuild.paths import normalize
from zombuild.tasks._default import ActionableTask
from dataclasses import dataclass
from pathlib import Path, PurePath

if TYPE_CHECKING:
    from zombuild import Invocation

_PathLike = str | PurePath | Path


class FilesTask(ActionableTask):
    """
    A task that enacts a set of filesystem operations.

    The `touch(...)` `file(...)` and `glob(...)` methods can be used by subclasses to describe the
    desired operations.

    Optionally, the constructor can be supplied with `srcroot` and `dstroot` paths. These will be
    used to resolve relative paths passed to the helper methods, and they are also prevent any
    operations that attempt to read or write from paths outside of the expected trees.

    While this task is not abstract, it is not suitable for direct use by projects.
    """

    type FileAction = Callable[[Path]]

    @dataclass
    class Item:
        src: FilesTask.FileAction | Path | None
        dst: Path

    def __init__(
        self,
        *,
        invocation: Invocation,
        name: str,
        mode: Literal["copy", "link"] = "copy",
        srcroot: Path | None = None,
        dstroot: Path | None = None,
    ) -> None:
        super().__init__(
            name=name,
            invocation=invocation,
        )
        self._mode: Literal["copy", "link"] = mode
        self._items: list[FilesTask.Item] = []

        if srcroot is not None:
            if not (srcroot := normalize(srcroot)).is_absolute():
                raise ZombuildException(f"{srcroot} is not absolute")
        if dstroot is not None:
            if not (dstroot := normalize(dstroot)).is_absolute():
                raise ZombuildException(f"{dstroot} is not absolute")

        self._srcroot = srcroot
        self._dstroot = dstroot

    def append(self, src: FileAction | Path | None, dst: Path):
        if self._srcroot is not None and isinstance(src, Path):
            if not src.is_relative_to(self._srcroot):
                raise ZombuildException(f"{src} is not relative to {self._srcroot}")
        if self._dstroot is not None:
            if not dst.is_relative_to(self._dstroot):
                raise ZombuildException(f"{dst} is not relative to {self._dstroot}")

        self._items.append(FilesTask.Item(src=src, dst=dst))

    @property
    def inputs(self) -> list[Path]:
        files = []
        for item in self._items:
            if isinstance(item, Path):
                files.append(item.src)
        return files

    @property
    def outputs(self) -> list[Path]:
        files = []
        for item in self._items:
            files.append(item.dst)
        return files

    def _relative(self, base: Path | None, leaf: _PathLike):
        if not isinstance(leaf, Path):
            leaf = Path(leaf)
        if not leaf.is_absolute():
            if base is None:
                raise ZombuildException(
                    f"{leaf} is not absolute and the relevant base is not set"
                )
            assert base.is_absolute()
            return normalize(base / leaf)
        else:
            return leaf

    def touch(self, dst: Path | str):
        self.append(None, self._relative(self._dstroot, dst))

    def file(self, src: FilesTask.FileAction | _PathLike | None, dst: _PathLike):
        if isinstance(src, _PathLike):
            src = self._relative(self._srcroot, src)

        self.append(
            src,
            self._relative(self._dstroot, dst),
        )

    def glob(
        self,
        src: _PathLike,
        dst: _PathLike,
        glob: str,
        ignore: str | list[str] | None = None,
    ):
        if ignore is None:
            ignore = []
        elif isinstance(ignore, str):
            ignore = [ignore]

        glob_root = self._relative(self._srcroot, src)

        for matched in glob_root.glob(glob):
            if matched.is_dir():
                continue
            for ignored in ignore:
                if matched.match(ignored):
                    break
                pass
            else:
                dst_path = dst / matched.relative_to(glob_root)
                self.file(src=matched, dst=dst_path)
        return self

    def execute(self) -> None:
        for item in self._items:
            if not item.dst.parent.exists():
                self.perform_work(
                    lambda: item.dst.parent.mkdir(parents=True),
                    f"create directory",
                    path=item.dst.parent,
                )

            if item.src is None:
                self.perform_work(
                    lambda: item.dst.touch(),
                    "touch file",
                    path=item.dst,
                )
                continue

            if isinstance(item.src, Callable):
                callable = item.src
                self.perform_work(
                    lambda: callable(item.dst),
                    "generate file",
                    path=item.dst,
                )
                continue

            if item.dst.exists():
                sstat = item.src.lstat()
                dstat = item.dst.lstat()
                if sstat.st_mtime <= dstat.st_mtime:
                    continue
                else:
                    dst = item.dst
                    self.perform_work(
                        lambda: dst.unlink(),
                        "delete file",
                        path=item.dst,
                    )

            if self._mode == "link":
                src = item.src
                dst = item.dst
                self.perform_work(
                    lambda: item.dst.symlink_to(src),
                    "create symlink",
                    source=item.src,
                    path=item.dst,
                )
            else:
                src = item.src
                dst = item.dst
                self.perform_work(
                    lambda: src.copy(dst, follow_symlinks=False),
                    "copy file",
                    source=item.src,
                    path=item.dst,
                )
