import os
from pathlib import Path, PurePath
from typing import overload


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
