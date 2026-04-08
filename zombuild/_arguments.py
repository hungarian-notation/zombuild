import pydantic
from pydantic import BeforeValidator, Field
from typing import Annotated, Any, Literal
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
