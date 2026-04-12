# Zombuild
# Copyright (C) 2026 Chris Bode and Zombuild Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from abc import ABC
from abc import abstractmethod
from typing import Protocol
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from zombuild._arguments import ZombuildArguments
    from ._invocation_plugins import InvocationPlugins
    from .config.package import PackageConfig
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
    def config(self) -> PackageConfig: ...

    @property
    @abstractmethod
    def console(self) -> Console: ...

    @property
    @abstractmethod
    def plugins(self) -> InvocationPlugins: ...

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
