from zombuild._exception import ZombuildException
from zombuild._invocation_plugins import Plugins
from zombuild.tasks import ZombuildTask


def create_task(
    plugins: Plugins,
    plugin_name: str,
    prototype_name: str,
    task_name: str,
    args: dict,
) -> ZombuildTask:

    plugin = plugins.plugin(plugin_name)
    factory = plugin.tasks.get(prototype_name)
    if factory is None:
        raise ZombuildException(f"no such task: {plugin_name}.{prototype_name}")
    args = dict(**plugin.options, **args)
    args["name"] = task_name
    task = factory(**args)
    return task
