from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Final

if TYPE_CHECKING:
    from zombuild._arguments import ZombuildArguments
    from zombuild._invocation import Invocation
    from zombuild.composite.component_accessors import ComponentAccessorsMixin
    from zombuild.config.package import PackageConfig


@dataclass(frozen=True, kw_only=True)
class ZombuildContext:
    invocation: Invocation
    arguments: ZombuildArguments
    project: Path | None
    features: ComponentAccessorsMixin
    config: PackageConfig | None = None


context: Final = ContextVar[ZombuildContext]("zombuild.context")


def context_invocation():
    return context.get().invocation


def context_arguments():
    return context.get().arguments


def context_project(required: bool = False):
    if (value := context.get().project) is None:
        raise ValueError("context config is not set")
    else:
        return value


def context_features():
    return context.get().features


def context_config(required: bool = False):
    if (value := context.get().config) is None:
        raise ValueError("context config is not set")
    else:
        return value


# invocation: Final   = ContextVar[Invocation]("zombuild.context.invocation")
# config: Final       = ContextVar[PackageConfig]("zombuild.context.config")
# project: Final      = ContextVar[Path]("zombuild.context.project")
# arguments: Final    = ContextVar[ZombuildArguments]("zombuild.context.arguments")
