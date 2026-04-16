from typing import Callable

from zombuild.composite.hooks import HookComponent


class SetupHook(HookComponent[Callable[[], None]]):
    pass
