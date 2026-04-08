from typing import TYPE_CHECKING, Callable, Literal


from zombuild.paths import normalize
from zombuild.tasks._default import ActionableTask
from dataclasses import dataclass
from pathlib import Path

if TYPE_CHECKING:
    from zombuild import Invocation


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
            assert (srcroot := normalize(srcroot)).is_absolute()
        if dstroot is not None:
            assert (dstroot := normalize(dstroot)).is_absolute()

        self._srcroot = srcroot
        self._dstroot = dstroot

    def log_work(self, work_type: str, **kwargs):

        super().log_work(work_type, **kwargs)

    def append(self, src: FileAction | Path | None, dst: Path):
        if self._srcroot is not None and isinstance(src, Path):
            assert src.is_relative_to(self._srcroot)
        if self._dstroot is not None:
            assert dst.is_relative_to(self._dstroot)

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

    def _relative(self, base: Path | None, leaf: str | Path):
        if not isinstance(leaf, Path):
            leaf = Path(leaf)
        if not leaf.is_absolute():
            assert base is not None
            assert base.is_absolute()
            return normalize(base / leaf)
        else:
            return leaf

    def touch(self, dst: Path | str):
        self.append(None, self._relative(self._dstroot, dst))

    def file(self, src: FilesTask.FileAction | Path | str | None, dst: Path | str):
        if isinstance(src, Path | str):
            src = self._relative(self._srcroot, src)

        self.append(
            src,
            self._relative(self._dstroot, dst),
        )

    def glob(
        self,
        src: Path | str,
        dst: Path | str,
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
                if not self.arguments.dry_run:
                    item.dst.parent.mkdir(parents=True)
                self.log_work(f"created directory", path=item.dst.parent)

            if item.src is None:
                if not self.arguments.dry_run:
                    item.dst.touch()
                self.log_work("touched file", path=item.dst)
                continue

            if isinstance(item.src, Callable):
                if not self.arguments.dry_run:
                    item.src(item.dst)
                self.log_work("generated file", path=item.dst)
                continue

            if item.dst.exists():
                sstat = item.src.lstat()
                dstat = item.dst.lstat()
                if sstat.st_mtime <= dstat.st_mtime:
                    continue
                else:
                    if not self.arguments.dry_run:
                        item.dst.unlink()
                    self.log_work("deleted file", path=item.dst)

            if self._mode == "link":
                if not self.arguments.dry_run:
                    item.dst.symlink_to(item.src)
                self.log_work("created symlink", source=item.src, path=item.dst)
            else:
                if not self.arguments.dry_run:
                    item.src.copy(item.dst, follow_symlinks=False)
                self.log_work("copied file", source=item.src, path=item.dst)
