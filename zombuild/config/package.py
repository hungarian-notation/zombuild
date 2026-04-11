from zombuild.config.withpath import WithPath
from zombuild.config.include import PathOrInclude
from zombuild.config.modinfo import MetaModDict, MetaPackageDict
from zombuild.config.plugin import PluginConfig
from zombuild.config.task import TaskConfig


from pydantic import ConfigDict, Field


from pathlib import Path
from typing import Any, Literal

from zombuild.config.types import OneOrSequence


class ModConfig(MetaModDict, WithPath):
    model_config = ConfigDict(extra="allow")
    versions: dict[str | Literal["common"], OneOrSequence[PathOrInclude]]


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
