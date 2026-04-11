from dataclasses import asdict, dataclass
import os
from zombuild._exception import ZombuildException
from pathlib import Path, PurePath
from typing import Any, Callable, Literal, Protocol, overload

import glob as libglob

_PathLike = str | PurePath | Path


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


def expand(path: str | PurePath | Path, base: Path = Path.cwd(), resolve=False):
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    path = os.path.normpath(base / path)
    if resolve:
        return Path(path).resolve()
    else:
        return Path(path)


def _pf(path: Any) -> str:
    if not isinstance(path, Path) or not path.is_absolute():
        return str(path)

    """
    formats a path for logging or display
    """
    try:
        path.relative_to(Path.cwd(), walk_up=True)
        return str(path)
    except:
        return str(path)


class Plan:
    """
    Builds and executes a set of planned filesystem operations.
    """

    _Ex = ZombuildException

    type FileAction = Callable[[Path]]

    @dataclass
    class Collected:
        abs: Path
        rel: PurePath

    @dataclass
    class PlanItem:
        src: Plan.FileAction | Path | None
        dst: Path

    class Listener(Protocol):
        def __call__(
            self, message: str, *, path: Path, source: Path | None = None
        ) -> Any: ...

    def __init__(
        self,
        *,
        srcroot: Path,
        dstroot: Path,
        mode: Literal["copy", "link"] = "copy",
        enforce_relative: Literal["src", "dst", "both"] | bool = "dst",
    ) -> None:

        if not (srcroot := normalize(srcroot)).is_absolute():
            raise self._Ex(f"srcroot '{_pf(srcroot)}' is not absolute")

        if not (dstroot := normalize(dstroot)).is_absolute():
            raise self._Ex(f"dstroot '{_pf(dstroot)}' is not absolute")

        self.mode: Literal["copy", "link"] = mode
        """
        when set to `"link"`, the planner will create symlinks to the source files where possible
        """

        self.items: list[Plan.PlanItem] = []

        self._src_root = srcroot
        self._dst_root = dstroot

        self.enforce_relative_src = enforce_relative in ("src", "both", True)
        self.enforce_relative_dst = enforce_relative in ("dst", "both", True)

    @property
    def srcroot(self):
        return self._src_root

    @property
    def dstroot(self):
        return self._dst_root

    def resolve_source(self, src: str | PurePath):
        return self._resolve(self.srcroot, src)

    def resolve_destination(self, dst: str | PurePath):
        return self._resolve(self.dstroot, dst)

    def _resolve(self, base: Path | None, leaf: _PathLike):
        if not isinstance(leaf, Path):
            leaf = Path(leaf)
        if not leaf.is_absolute():
            if base is None:
                raise self._Ex(
                    f"{_pf(leaf)} is not absolute and the relevant base is not set"
                )
            if not base.is_absolute():
                raise self._Ex(f"{base} is not absolute")
            return normalize(base / leaf)
        else:
            return leaf

    def append(self, src: FileAction | Path | None, dst: Path):
        if self.enforce_relative_src and isinstance(src, Path):
            if not src.is_relative_to(self._src_root):
                raise self._Ex(f"{_pf(src)} is not relative to {self._src_root}")
        if self.enforce_relative_dst:
            if not dst.is_relative_to(self._dst_root):
                raise self._Ex(f"{_pf(dst)} is not relative to {self._dst_root}")

        assert not isinstance(src, Path) or src.is_absolute()
        assert dst.is_absolute()

        for item in self.items:
            if item.dst == dst:
                if item.src == src:
                    ex = self._Ex(f"duplicate entries for {_pf(src)}->{_pf(dst)}")
                else:
                    ex = self._Ex(f"multiple input paths for output: {_pf(dst)}")
                ex.add_note(f"source: {item.src}")
                ex.add_note(f"source: {src}")
                raise ex

        self.items.append(Plan.PlanItem(src=src, dst=dst))

    @property
    def inputs(self) -> list[Path]:
        files = []
        for item in self.items:
            if isinstance(item, Path):
                files.append(item.src)
        return files

    @property
    def outputs(self) -> list[Path]:
        files = []
        for item in self.items:
            files.append(item.dst)
        return files

    def touch(self, dst: Path | str):
        self.append(None, self._resolve(self._dst_root, dst))

    def file(self, src: Plan.FileAction | _PathLike | None, dst: _PathLike):
        if isinstance(src, _PathLike):
            src = self._resolve(self._src_root, src)
        self.append(
            src,
            self._resolve(self._dst_root, dst),
        )

    def collect(
        self,
        src: _PathLike,
        glob: str,
        ignore: str | list[str] | None = None,
        *,
        allow_magic: bool = False,
    ) -> list[Collected]:
        """
        Collects the list of path pairs described by the arguments.

        Args:
            src: The source to match from. This controls which portion of the matched path is
                retained when translated to a destination path.

                If given as a relative path, that path will be resolved against :attr:`srcroot`.
                If `allow_magic_src` is True, `src` will be expanded as a glob pattern.

            glob: glob pattern to match from src.
            ignore: _description_. Defaults to None.
            allow_magic_src: _description_. Defaults to False.

        Raises:
            self._Ex: _description_

        Returns:
            _description_
        """

        if libglob.has_magic(str(src)):
            if not allow_magic:
                raise self._Ex(f"unexpected magic characters in src: {_pf(src)}")
            else:
                srcs = libglob.glob(str(src), root_dir=self.srcroot, recursive=True)
                collected: list[Plan.Collected] = []
                for next_src in srcs:
                    next_src = self.resolve_source(next_src)
                    assert next_src.is_absolute(), str(next_src)
                    if next_src.is_dir():
                        collected_here = self.collect(
                            src=next_src,
                            glob=glob,
                            ignore=ignore,
                            allow_magic=False,
                        )
                        for each in collected_here:
                            collected.append(
                                self.Collected(each.abs, each.abs.relative_to(next_src))
                            )
                return collected

        glob_root = self._resolve(self._src_root, src)
        if ignore is None:
            ignore = []
        elif isinstance(ignore, str):
            ignore = [ignore]

        collected: list[Plan.Collected] = []

        for matched in glob_root.glob(glob):
            if matched.is_dir():
                continue
            for ignored in ignore:
                if matched.match(ignored):
                    continue
            collected.append(
                self.Collected(
                    abs=matched,
                    rel=matched.relative_to(glob_root),
                )
            )

        return collected

    def glob(
        self,
        src: _PathLike,
        dst: _PathLike,
        glob: str,
        ignore: str | list[str] | None = None,
        *,
        allow_magic_src: bool = False,
    ):
        collected = self.collect(
            src=src, glob=glob, ignore=ignore, allow_magic=allow_magic_src
        )
        dst = self._resolve(self._dst_root, dst)
        for pair in collected:
            self.file(pair.abs, dst / pair.rel)

    def execute(
        self, *, listener: Listener | None = None, perform_operations: bool = True
    ) -> None:

        def _auditable(
            work: Callable,
            message: str,
            path: Path,
            source: Path | None = None,
        ):
            if perform_operations:
                work()
            if listener:
                listener(message=message, path=path, source=source)

        for item in self.items:
            if not item.dst.parent.exists():
                _auditable(
                    lambda: item.dst.parent.mkdir(parents=True),
                    f"create directory",
                    path=item.dst.parent,
                )

            if item.src is None:
                _auditable(
                    lambda: item.dst.touch(),
                    "touch file",
                    path=item.dst,
                )
                continue

            if isinstance(item.src, Callable):
                callable = item.src
                _auditable(
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
                    _auditable(
                        lambda: dst.unlink(),
                        "delete file",
                        path=item.dst,
                    )

            if self.mode == "link":
                src = item.src
                dst = item.dst
                _auditable(
                    lambda: item.dst.symlink_to(src),
                    "create symlink",
                    source=item.src,
                    path=item.dst,
                )
            else:
                src = item.src
                dst = item.dst
                _auditable(
                    lambda: src.copy(dst, follow_symlinks=False),
                    "copy file",
                    source=item.src,
                    path=item.dst,
                )
