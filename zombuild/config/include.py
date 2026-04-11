from typing import Self, Sequence


from pydantic import BaseModel, Field

type IncludeLike = str | IncludeConfig
type BuildActionLike = str | IncludeConfig | BuildConfig


class IncludeConfig(BaseModel):
    source: str
    prefix: str
    include: str | list[str] = Field(default_factory=lambda: ["**/*"])
    ignore: str | list[str] = Field(default_factory=list)

    @classmethod
    def convert(cls, string: str | IncludeConfig) -> IncludeConfig:
        if isinstance(string, IncludeConfig):
            return string
        return IncludeConfig(
            source=string,
            prefix="",
            include="**/*",
            ignore=[],
        )

    @classmethod
    def convert_list(
        cls, include: str | IncludeConfig | Sequence[str | IncludeConfig]
    ) -> list[IncludeConfig]:
        if isinstance(include, str):
            return [IncludeConfig.convert(include)]
        elif isinstance(include, IncludeConfig):
            return [include]
        else:
            return [IncludeConfig.convert(item) for item in include]


class BuildConfig(BaseModel):
    action: str = "default"
    target: IncludeLike | Sequence[IncludeLike]

    @classmethod
    def convert(
        cls, string: BuildConfig | IncludeLike | Sequence[IncludeLike]
    ) -> BuildConfig:
        if isinstance(string, BuildConfig):
            return string
        return BuildConfig(target=IncludeConfig.convert_list(string))

    @classmethod
    def convert_list(
        cls,
        include: BuildConfig | IncludeLike | Sequence[IncludeLike | BuildConfig],
    ) -> list[BuildConfig]:
        if isinstance(include, str | IncludeConfig):
            return [BuildConfig.convert(include)]
        elif isinstance(include, BuildConfig):
            return [include]
        else:
            return [BuildConfig.convert(item) for item in include]
