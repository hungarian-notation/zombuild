from pydantic import BaseModel, ConfigDict


class PluginConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    plugin: str

    @staticmethod
    def convert(value: "str|PluginConfig"):
        if isinstance(value, PluginConfig):
            return value
        else:
            return PluginConfig(plugin=value)