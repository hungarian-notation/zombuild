from typing import TYPE_CHECKING, Any,  Protocol, runtime_checkable

if TYPE_CHECKING:
    from zombuild.plugins import ZombuildPlugin

_PLUGIN_ATTR = "$zombuild_plugin"

class PluginFactory[T: ZombuildPlugin](Protocol):
    def __call__(self, **kwds: Any) -> T: ...

def plugin(**kwargs):

    def decorator[T: ZombuildPlugin](entry: PluginFactory[T]):
        setattr(entry, _PLUGIN_ATTR, {"entry": entry})
        return entry

    return decorator
