from zombuild.composite._collect_components import components
from zombuild.composite.component import Composite
from zombuild.composite.types import Component


class component_filter[T: Component]:
    def __init__(self, feature_type: type[T]) -> None:
        self.feature_type = feature_type
        pass

    def __get__(self, obj: Composite, objtype=None):
        return components(obj, predicate=self.feature_type)
