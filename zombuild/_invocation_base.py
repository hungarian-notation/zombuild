from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol


if TYPE_CHECKING:
    from pathlib import Path
    from zombuild._arguments import ZombuildArguments
    from ._invocation_plugins import InvocationPlugins
    from .config import PackageModel
    from .console import Console
    from .tasks import LifecycleTask


class InvocationBase(ABC):

    # PROPERTIES

    @property
    @abstractmethod
    def arguments(self) -> ZombuildArguments: ...

    @property
    @abstractmethod
    def project_dir(self) -> Path: ...

    @property
    @abstractmethod
    def config(self) -> PackageModel: ...

    @property
    @abstractmethod
    def console(self) -> Console: ...

    @property
    @abstractmethod
    def loader(self) -> InvocationPlugins: ...

    # LOGGING

    def info(self, *message: object):
        if self.arguments.verbose >= 0:
            self.console.print(*message)

    def verbose(self, *message: object):
        if self.arguments.verbose > 0:
            self.console.print(*message)

    def trace(self, *message: object):
        if self.arguments.verbose > 1:
            self.console.print(*message)
