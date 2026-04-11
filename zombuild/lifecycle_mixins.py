from typing import Iterable


class WithSetupLifecycle[**P]:
    def setup_early(self, *args: P.args, **kwargs: P.kwargs):
        pass

    def setup(self, *args: P.args, **kwargs: P.kwargs):
        pass

    def setup_late(self, *args: P.args, **kwargs: P.kwargs):
        pass


def execute_setup[**P](
    objects: Iterable[WithSetupLifecycle[P]], *args: P.args, **kwargs: P.kwargs
):
    for object in objects:
        object.setup_early(*args, **kwargs)
    for object in objects:
        object.setup(*args, **kwargs)
    for object in objects:
        object.setup_late(*args, **kwargs)
