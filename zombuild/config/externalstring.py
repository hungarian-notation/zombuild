from zombuild.config.withpath import WithPath


from pydantic import BaseModel, ConfigDict


from typing import overload


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