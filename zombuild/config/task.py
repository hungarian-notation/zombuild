from pydantic import BaseModel, ConfigDict


class TaskConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str