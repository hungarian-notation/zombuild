from pydantic import BaseModel

from pathlib import Path
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