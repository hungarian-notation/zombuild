from pathlib import Path
import sys
import zombuild

from zombuild import paths
from zombuild.config import PackageModel
from zombuild.plugins import ZombuildPlugin
from zombuild import Invocation
from zombuild.tasks import TaskNameFilter

from zombuild_core.InstallTask import InstallTask, UninstallTask
from .BuildTask import BuildTask
from .CleanTask import CleanTask


class CorePlugin(ZombuildPlugin):

    def __init__(self, invocation: Invocation, **kwargs) -> None:
        super().__init__(
            "core",
            target=kwargs.get("target", invocation.config.output),
        )

        self.register_task(BuildTask)

        self.register_task(CleanTask)
        self.register_task(InstallTask)
        self.register_task(UninstallTask)

    def setup(self, invocation: Invocation) -> None:
        output_path = paths.expand(invocation.config.output, invocation.project_dir)
        # print(f"target={target}")

        self.task_clean = invocation.register_task(
            CleanTask(
                invocation=invocation,
                name="clean-mod",
                output_path=output_path,
            )
        )

        self.task_build = invocation.register_task(
            BuildTask(
                invocation=invocation,
                name="build-mod",
                output_path=output_path,
            )
        )

        self.task_install = invocation.register_task(
            InstallTask(
                invocation=invocation,
                name="install-mod",
                output_path=output_path,
            )
        )

        self.task_uninstall = invocation.register_task(
            UninstallTask(
                invocation=invocation,
                name="uninstall-mod",
                output_path=output_path,
            )
        )

        self.task_build.depends_on(self.task_clean, optional=True)
        self.task_install.depends_on(self.task_build)
        self.task_clean.depends_on(self.task_uninstall)


@zombuild.plugin()
def plugin(invocation: Invocation, **kwargs):

    plugin = CorePlugin(
        invocation=invocation,
        target=kwargs.get("target", invocation.config.output),
    )

    return plugin
