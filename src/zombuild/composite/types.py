
from zombuild.composite.component import Component
from zombuild.composite.component import Composite

type CollectComponentTarget = (
    Component | Composite
)  # | Iterable[CollectComponentTarget]
