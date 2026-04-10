from pathlib import Path
from typing import Any, Literal, overload
from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

VERSION = r"^[0-9]+(\.[0-9]+){1,2}$"


class PluginConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    plugin: str

    @staticmethod
    def convert(value: "str|PluginConfig"):
        if isinstance(value, PluginConfig):
            return value
        else:
            return PluginConfig(plugin=value)


class TaskConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str


class WithPath(BaseModel):
    _json_source: SkipJsonSchema[Path | None] = None

    @property
    def source(self) -> Path:
        if self._json_source is None:
            raise Exception("stable property `source` was not set")
        return self._json_source

    @source.setter
    def source(self, path: Path):
        if self._json_source is not None:
            raise Exception("stable property `source` was already set")
        self._json_source = path


class ExternalString(BaseModel):
    model_config = ConfigDict(title="", extra="forbid")

    ref: str

    def path(self, context: WithPath):
        return context.source.parent / self.ref

    def get(self, context: WithPath):
        return self.path(context).read_text()

    @staticmethod
    @overload
    def resolve(value: "str|ExternalString", context: WithPath) -> str: ...

    @staticmethod
    @overload
    def resolve(value: "str|ExternalString|None", context: WithPath) -> str | None: ...

    @staticmethod
    def resolve(value: "str|ExternalString|None", context: WithPath) -> str | None:
        if value is None:
            return None
        elif isinstance(value, str):
            return value
        else:
            return value.get(context)


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

    pack: str | list[str] | None = Field(default_factory=list)
    tiledef: str | list[str] | None = Field(default_factory=list)


class ModConfig(MetaModDict, WithPath):
    model_config = ConfigDict(extra="allow")
    common: str | None = None
    versions: dict[str, str]


class PackageModel(MetaPackageDict, WithPath):
    model_config = ConfigDict(extra="ignore")

    schema_reference: str | None = Field(default=None, alias="$schema")
    "schema path/uri"

    id: str
    name: str
    version: str
    preview: str
    mods: dict[str, ModConfig] = Field(min_length=1)

    plugins: list[str | PluginConfig] = Field(
        default_factory=list, examples=[["core"], [{"plugin": "core", "args": {}}]]
    )
    tasks: dict[str, str | TaskConfig] = Field(
        default_factory=dict,
        examples=[
            {
                "build": "core.build",
                "clean": "core.clean",
                "clean-build": ["clean", "build"],
            }
        ],
    )

    output: str | Path = Field(
        description="output path (used by core plugin)", default="dist"
    )

    def __init__(self, **kwds: Any) -> None:
        super().__init__(**kwds)

        if "source" in kwds:
            self.source = kwds["source"]
            for mod in self.mods.values():
                mod.source = self.source
