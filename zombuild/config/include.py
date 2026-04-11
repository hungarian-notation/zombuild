from typing import Sequence

from zombuild.config.types import OneOrSequence


from pydantic import BaseModel, Field

type PathOrInclude = str | Include


def normalize_include(include: PathOrInclude):
    if isinstance(include, str):
        return Include.from_string(include)
    else:
        return include


def normalize_includes(include: OneOrSequence[PathOrInclude]):
    if isinstance(include, str | Include):
        return [normalize_include(include)]
    else:
        return [normalize_include(item) for item in include]


class Include(BaseModel):
    source: str
    prefix: str

    include: OneOrSequence[str] = Field(default_factory=lambda: ["**/*"])
    ignore: OneOrSequence[str] = Field(default_factory=list)

    @classmethod
    def from_string(cls, string: str):
        return Include(
            source=string,
            prefix="",
            include="**/*",
            ignore=[],
        )
