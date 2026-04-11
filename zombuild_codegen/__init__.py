
from pydantic import BaseModel, ValidationError

import zombuild

from zombuild import Invocation, ZombuildPlugin
from zombuild import paths
from zombuild._exception import ZombuildConfigException
from zombuild.tasks import ActionableTask

from zombuild_core import CorePlugin


class EnumConfig(BaseModel):
    type: str
    glob: str
    output: str


class EnumsTask(ActionableTask):
    """
    Generates Lua enumerations from glob pattern matches.
    """

    _HEADER = "-- generated source file: do not edit directly"

    def __init__(
        self,
        invocation: Invocation,
        enums: list[dict],
        **extra,
    ) -> None:
        super().__init__(invocation=invocation, **extra)

        if not isinstance(enums, list):
            raise TypeError("expected `enums` to be a list")

        enum_models: list[EnumConfig] = []

        for item in enums:
            try:
                enum_models.append(EnumConfig(**item))
            except ValidationError as e:
                raise ZombuildConfigException(
                    f"invalid enum config",
                    validation_error=e,
                )

        self.enums = enum_models

    def setup(self, invocation: Invocation) -> None:
        invocation.lifecycle_task("build").depends_on(self)
        invocation.require_task(CorePlugin.BUILD_TASK).depends_on(self)

    def execute(self) -> None:
        for enum in self.enums:
            self.generate(enum)

    def generate(self, enum: EnumConfig):
        output = paths.expand(enum.output, self.invocation.project_dir)
        source = self.get_source(enum)

        if not output.parent.exists():

            self.perform_work(
                lambda: output.parent.mkdir(parents=True),
                "create directory",
                path=output.parent,
            )

        if output.exists():
            if not output.is_file():
                raise Exception(f"enum output is an existing non-file: {output}")

            existing = output.read_text()

            if existing.strip() == source.strip():
                self.log_verbose(
                    f"skipping enum {enum.type}: existing source is identical"
                )
                return

            if not existing.startswith(self._HEADER):
                raise Exception(
                    f"output appears to be an existing file "
                    "that is not a generated enum: {output}"
                )
            else:
                self.perform_work(
                    lambda: output.unlink(),
                    "unlink old enum",
                    path=output,
                )

        assert not output.exists()

        self.perform_work(
            lambda: output.write_text(source),
            "write generated enum",
            path=output,
        )

    def get_source(self, enum: EnumConfig):
        variable_name = enum.type.replace(".", "_").lower()
        lines: list[str] = []
        lines.append(self._HEADER)
        lines.append(f"")
        lines.append(f"---@enum {enum.type}")
        lines.append(f"local {variable_name} = {{")
        for matched in self.invocation.project_dir.glob(enum.glob):
            enum_value = matched.stem
            enum_key = enum_value.upper().replace("-", "_")
            enum_assinment = f'    {enum_key.ljust(33)} = "{enum_value}",'
            lines.append(enum_assinment)
        lines.append("}")
        lines.append("")
        lines.append(f"return {variable_name}")
        return "\n".join(lines)


class CodeGenPlugin(ZombuildPlugin):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.register_task(EnumsTask)


@zombuild.plugin()
def plugin(invocation: Invocation, **kwargs):

    plugin = CodeGenPlugin(invocation=invocation)

    return plugin
