import importlib
import importlib.util
from importlib.machinery import ModuleSpec

from typing import TYPE_CHECKING
from types import ModuleType

from ._decorator import _PLUGIN_ATTR, PluginFactory

if TYPE_CHECKING:
    from zombuild._invocation import Invocation
    from zombuild.tasks._task import ZombuildTask


class ZombuildPlugin:
    def __init__(self, id: str, **kwargs) -> None:
        super().__init__()

        self.task_prototypes: dict[str, type[ZombuildTask]] = dict()
        self._id = id
        self._options = kwargs

    @property
    def module_name(self):
        return self.id

    @property
    def id(self):
        return self._id

    @property
    def options(self):
        return self._options

    def register_task(self, factory: type[ZombuildTask]):
        self.task_prototypes[factory.__name__] = factory

    def setup(self, invocation: Invocation) -> None: ...

    @classmethod
    def load(cls, package_name: str) -> PluginFactory:
        search = [f"zombuild_{package_name}", package_name]
        package: ModuleType | None = None

        for candidate in search:
            spec: ModuleSpec | None = importlib.util.find_spec(candidate)

            if spec is not None:
                package = importlib.import_module(spec.name)
                for membername in dir(package):
                    member = getattr(package, membername)
                    if hasattr(member, _PLUGIN_ATTR):
                        return member
        else:
            if package is None:
                raise Exception(f"no such package {package_name}")
            else:
                name = package.__name__
                raise Exception(f"package {name} does not define a plugin")
