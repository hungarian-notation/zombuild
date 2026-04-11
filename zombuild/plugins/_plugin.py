from abc import ABC, abstractmethod
import importlib
import importlib.util
from importlib.machinery import ModuleSpec

import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    Sequence,
    TypeGuard,
    final,
    overload,
    override,
)
from types import ModuleType

from zombuild._exception import ZombuildException
from .features import (
    OptionsFeature,
    PluginFeature,
    TaskFeature,
)

from ._decorator import _PLUGIN_ATTR, PluginFactory

if TYPE_CHECKING:
    from zombuild._invocation import Invocation
    from zombuild.tasks._task import ZombuildTask


class FeatureAccessors(ABC):
    @property
    @abstractmethod
    def features(self) -> list[PluginFeature]: ...

    @overload
    def get_feature[T](self, type: type[T], /) -> T | None: ...

    @overload
    def get_feature[T: PluginFeature](
        self, typeguard: Callable[[PluginFeature], TypeGuard[T]], /
    ) -> T | None: ...

    @overload
    def get_feature(
        self, predicate: Callable[[PluginFeature], bool], /
    ) -> PluginFeature | None: ...

    def get_feature(self, predicate: type | Callable[[PluginFeature], bool]) -> Any:
        if isinstance(predicate_type := predicate, type):
            predicate = lambda feature: isinstance(feature, predicate_type)

        for attr in self.features:
            if predicate(attr):
                return attr
        else:
            return None

    @overload
    def get_features[T](self, type: type[T], /) -> Sequence[T]: ...

    @overload
    def get_features[T: PluginFeature](
        self, typeguard: Callable[[PluginFeature], TypeGuard[T]], /
    ) -> Sequence[T]: ...

    @overload
    def get_features(
        self, predicate: Callable[[PluginFeature], bool], /
    ) -> Sequence[PluginFeature]: ...

    def get_features(
        self, predicate: type | Callable[[PluginFeature], bool], /
    ) -> Sequence[Any]:
        if isinstance(predicate, type):
            return [attr for attr in self.features if isinstance(attr, predicate)]
        else:
            return [attr for attr in self.features if predicate(attr)]

    def has_feature(self, predicate: type | Callable[[PluginFeature], bool]):
        return len(self.get_features(predicate)) > 0


class ZombuildPlugin(FeatureAccessors):
    """
    Base class implemented by all plugins.

    A plugin is chiefly a collection of PluginAttributes that describe what
    """

    def __init__(self, *, id: str | None = None, **kwargs) -> None:
        self._features: list[PluginFeature] = []

        if id is None:
            module = inspect.getmodule(self.__class__)
            package = module.__package__ if module else None
            if package is not None:
                id = package
                if id.startswith("zombuild_"):
                    id = id.removeprefix("zombuild_")

        if id is None:
            raise ZombuildException(f"could not infer plugin id: {self}")

        self._id = id

        if kwargs:
            self.add_feature(OptionsFeature(self, kwargs))

    @property
    @override
    def features(self):
        return self._features

    @property
    def id(self):
        return self._id

    @property
    def options(self) -> dict[str, Any]:
        attr = self.get_feature(OptionsFeature)
        if attr:
            return attr.options
        else:
            return {}

    @property
    def tasks(self):
        tasks: dict[str, type[ZombuildTask]] = {}
        for attr in self.get_features(TaskFeature):
            tasks[attr.alias] = attr.task
        return tasks

    def add_feature(self, attr: PluginFeature, /):
        self.features.append(attr)

    # def where(self, predicate: Callable[[PluginAttribute], bool]):
    #     return [attr for attr in self.attributes if predicate(attr)]

    def register_task(self, factory: type[ZombuildTask], *, alias: str | None = None):
        """
        Registers a task type that can be instantiated by the user via the package.tasks json
        object.

        Args:
            factory: The task's type.
                Its constructor will be invoked with the arguments provided by the user.
            alias: The task's type name at runtime.
                If `None`, the name of the task type will be used.
                Defaults to `None`.
        """
        self.add_feature(TaskFeature(self, factory, alias))

    @classmethod
    def load(cls, package_name: str, /) -> PluginFactory:
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
