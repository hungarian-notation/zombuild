import zombuild

from zombuild import paths
from zombuild.plugins import ZombuildPlugin
from zombuild import Invocation

from zombuild.plugins.features import DefaultTaskFeature
from zombuild_core.InstallTask import InstallTask, UninstallTask
from zombuild_core.action_provider import ActionProviderFeature
from .BuildTask import BuildTask, default_action, json_merge_action
from .CleanTask import CleanTask


def output_path(invocation: Invocation):
    return paths.expand(invocation.config.output, invocation.project_dir)


class CorePlugin(ZombuildPlugin):

    CLEAN_TASK = "clean-mod"
    BUILD_TASK = "build-mod"
    INSTALL_TASK = "install-mod"
    UNINSTALL_TASK = "uninstall-mod"

    def __init__(self, invocation: Invocation, **kwargs) -> None:
        self.target = kwargs.get("target", invocation.config.output)

        super().__init__(
            target=self.target,
        )

        self.register_task(BuildTask)
        self.register_task(CleanTask)
        self.register_task(InstallTask)
        self.register_task(UninstallTask)

        self.add_feature(DefaultTaskFeature(self.create_defaults, self.wire_defaults))
        self.add_feature(ActionProviderFeature(self, "default", default_action))
        self.add_feature(ActionProviderFeature(self, "json-merge", json_merge_action))

    def wire_defaults(self, invocation: Invocation):
        self.task_build.depends_on(self.task_clean, optional=True)
        self.task_install.depends_on(self.task_build)
        self.task_clean.depends_on(self.task_uninstall)

    def create_defaults(self, invocation: Invocation) -> None:
        self.task_clean = invocation.register_task(
            CleanTask(
                invocation=invocation,
                name=self.CLEAN_TASK,
                output_path=output_path(invocation),
            )
        )

        self.task_build = invocation.register_task(
            BuildTask(
                invocation=invocation,
                name=self.BUILD_TASK,
                output_path=output_path(invocation),
            )
        )

        self.task_install = invocation.register_task(
            InstallTask(
                invocation=invocation,
                name=self.INSTALL_TASK,
                output_path=output_path(invocation),
            )
        )

        self.task_uninstall = invocation.register_task(
            UninstallTask(
                invocation=invocation,
                name=self.UNINSTALL_TASK,
                output_path=output_path(invocation),
            )
        )


@zombuild.plugin()
def plugin(invocation: Invocation, **kwargs):

    plugin = CorePlugin(
        invocation=invocation,
        target=kwargs.get("target", invocation.config.output),
    )

    return plugin
