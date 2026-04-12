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
from typing import overload

from pydantic import BaseModel
from pydantic import ConfigDict

from zombuild.config.withpath import WithPath


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
