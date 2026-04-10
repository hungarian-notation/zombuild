from typing import Sequence

from zombuild.config._types import ItemOrSequence
from zombuild.config.definitions import glob_default, ignore_default


from pydantic import BaseModel, Field

type PathOrInclude = str | Include


def normalize_include(include: PathOrInclude):
    if isinstance(include, str):
        return Include.from_string(include)
    else:
        return include


def normalize_includes(include: ItemOrSequence[PathOrInclude]):
    if isinstance(include, str | Include):
        return [normalize_include(include)]
    else:
        return [normalize_include(item) for item in include]


class Include(BaseModel):
    source: str
    prefix: str

    include: ItemOrSequence[str] = Field(default_factory=glob_default)
    ignore: ItemOrSequence[str] = Field(default_factory=ignore_default)

    @classmethod
    def from_string(cls, string: str):
        return Include(
            source=string,
            prefix="",
            include=glob_default(),
            ignore=ignore_default(),
        )
