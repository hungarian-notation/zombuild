from pathlib import Path

from zombuild import paths
from zombuild import Invocation
from zombuild.tasks import ActionableTask


class InstallTask(ActionableTask):

    def __init__(
        self,
        *,
        invocation: Invocation,
        output_path: Path,
        name: str,
        **extra,
    ) -> None:
        super().__init__(
            invocation=invocation,
            name=name,
        )
        self.output_path = output_path

        invocation.lifecycle_task("install").depends_on(self)

    def execute(self) -> None:
        workshop_path = paths.expand(
            self.invocation.arguments.workshop,
            self.invocation.project_dir,
        )

        install_path = workshop_path / self.invocation.config.id

        # print(f"output_path={self.output_path}")
        # print(f"workshop_path={workshop_path}")
        # print(f"install_path={install_path}")

        if install_path.is_symlink() and not install_path.exists(follow_symlinks=True):
            install_path.unlink()
            self.log_work("unlinking broken symlink", path=install_path)

        if install_path.exists(follow_symlinks=False):
            if install_path.is_symlink():
                if install_path.resolve() == self.output_path.resolve():
                    return
            raise Exception(f"install path already exists: {install_path}")

        self.log_work("linking", path=install_path, source=self.output_path)
        install_path.symlink_to(self.output_path, True)


class UninstallTask(ActionableTask):

    def __init__(
        self,
        *,
        invocation: Invocation,
        output_path: Path,
        name: str,
        **extra,
    ) -> None:
        super().__init__(
            invocation=invocation,
            name=name,
        )
        self.output_path = output_path

    def execute(self) -> None:
        workshop_path = paths.expand(
            self.invocation.arguments.workshop,
            self.invocation.project_dir,
        )

        install_path = workshop_path / self.invocation.config.id

        # print(f"output_path={self.output_path}")
        # print(f"workshop_path={workshop_path}")
        # print(f"install_path={install_path}")

        if install_path.is_symlink() and not install_path.exists(follow_symlinks=True):
            install_path.unlink()
            self.log_work("unlinking broken symlink", path=install_path)

        if install_path.exists(follow_symlinks=False):
            if install_path.is_symlink():
                if install_path.resolve() == self.output_path.resolve():
                    self.log_work("unlinking", path=install_path)
                    install_path.unlink()
                    return

            raise Exception(f"install path is not expected symlink: {install_path}")
