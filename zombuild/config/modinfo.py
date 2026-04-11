from zombuild.config.externalstring import ExternalString
from pydantic import BaseModel, Field
from typing import Literal

VERSION = r"^[0-9]+(\.[0-9]+){1,2}$"


class PackageInfoConfig(BaseModel):
    """
    Properties used to build mod.info that are possibly common to the entire
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


class ModInfoConfig(PackageInfoConfig):
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

    pack: str | list[str] = Field(default_factory=list)
    tiledef: str | list[str] = Field(default_factory=list)
