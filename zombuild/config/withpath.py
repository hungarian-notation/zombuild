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
from pathlib import Path

from pydantic import BaseModel
from pydantic.json_schema import SkipJsonSchema


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
