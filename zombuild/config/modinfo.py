
from zombuild.config.externalstring import ExternalString
from pydantic import BaseModel, Field
from typing import Literal
from zombuild.config.types import OneOrSequence

VERSION = r"^[0-9]+(\.[0-9]+){1,2}$"


class MetaPackageDict(BaseModel):
    # model_config = ConfigDict(extra="forbid")

    """
    Properties used to build mod.info that are likely common to the entire
    package.
    """

    authors: list[str] = Field(default_factory=list, description="mod.info authors")
    url: str | None = Field(default=None, description="mod.info url")
    description: str | ExternalString = Field(
        frozen=True,
        default="",
        description="mod.info description",
    )
    category: Literal["map", "vehicle", "features", "modpack"] | None = None
    versionMin: str | None = Field(default=None, pattern=VERSION)
    versionMax: str | None = Field(default=None, pattern=VERSION)

    require: list[str] = Field(default_factory=list)
    incompatible: list[str] = Field(default_factory=list)


class MetaModDict(MetaPackageDict):
    # model_config = ConfigDict(extra="forbid")

    """
    Properties used to build mod.info
    """

    # id: str
    name: str | None = None
    poster: str

    modversion: str | None = None
    """defaults to required version from package"""

    icon: str | None = None
    """will use the poster if not specified"""

    loadModAfter: list[str] = Field(default_factory=list)
    loadModBefore: list[str] = Field(default_factory=list)

    pack: OneOrSequence[str] = Field(default_factory=list)
    tiledef: OneOrSequence[str] = Field(default_factory=list)
