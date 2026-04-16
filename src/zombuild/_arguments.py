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

from typing import Annotated
from typing import Any
from typing import Literal

import pydantic
from pydantic import BeforeValidator
from pydantic import Field
from pydantic_core import PydanticUseDefault


def default_if_none(value: Any) -> Any:
    if value is None:
        raise PydanticUseDefault()
    return value


class ZombuildArguments(pydantic.BaseModel):
    project: str

    properties: dict = Field(
        default_factory=dict,
    )

    workshop: Annotated[str, BeforeValidator(default_if_none)] = "~/Zomboid/Workshop"

    verbose: int

    command: None | Literal["list", "run", "schema"] = None

    tasks: list[str] = Field(default_factory=list)

    list_types: bool = False

    dry_run: bool = False

    symlink: bool = True
