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
# from ._builder import Builder

__version__ = "0.0.3"

from .config import *
from .plugins import *

from ._package import resolve_package
from ._arguments import ZombuildArguments
from .__main__ import main

from ._invocation import Invocation, Tasks, Theme
from ._invocation_base import InvocationBase
from ._invocation_plugins import InvocationPlugins

from .fs import Plan
