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
from typing import Any
from typing import Protocol
from typing import runtime_checkable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zombuild.plugins import ZombuildPlugin

_PLUGIN_ATTR = "$zombuild_plugin"


class PluginFactory[T: ZombuildPlugin](Protocol):
    def __call__(self, **kwds: Any) -> T: ...


def plugin(**kwargs):

    def decorator[T: ZombuildPlugin](entry: PluginFactory[T]):
        setattr(entry, _PLUGIN_ATTR, {"entry": entry})
        return entry

    return decorator
