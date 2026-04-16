from dataclasses import dataclass
from typing import Callable
from typing import Iterable

from zombuild.composite._collect_components import components
from zombuild.composite.component import Composite
from zombuild.composite.types import Component


@dataclass(frozen=True)
class HookComponent[T: Callable](Component):
    early: T | None = None
    hook: T | None = None
    late: T | None = None

    def invoke_early[**P, R](
        self: HookComponent[Callable[P, R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ):
        if self.early:
            self.early(*args, **kwargs)

    def invoke[**P, R](
        self: HookComponent[Callable[P, R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ):
        if self.hook:
            self.hook(*args, **kwargs)

    def invoke_late[**P, R](
        self: HookComponent[Callable[P, R]],
        *args: P.args,
        **kwargs: P.kwargs,
    ):
        if self.late:
            self.late(*args, **kwargs)


def has_behavior(hook: HookComponent):
    if hook.early:
        return True
    if hook.hook:
        return True
    if hook.late:
        return True
    return False


def execute_hook[**P, R](
    hook: type[HookComponent[Callable[P, R]]],
    over: Iterable[Component | Composite],
    *args: P.args,
    **kwargs: P.kwargs,
) -> Iterable[R]:
    sequence = list(over)

    results: list[R | None] = []

    _components = [
        matched for comp in sequence for matched in components(comp, predicate=hook)
    ]

    targets: list[HookComponent[Callable[P, R]]] = list(
        matched for matched in _components if has_behavior(matched)
    )

    for i, target in enumerate(targets):
        result = target.early(*args, **kwargs) if target.early is not None else None
        if result is not None:
            results[i] = result

    for i, target in enumerate(targets):
        result = target.hook(*args, **kwargs) if target.hook is not None else None
        if result is not None:
            results[i] = result

    for i, target in enumerate(targets):
        result = target.late(*args, **kwargs) if target.late is not None else None
        if result is not None:
            results[i] = result

    return (result for result in results if result is not None)
