from zombuild.config.include import BuildConfig, IncludeConfig
from zombuild_core.BuildTask import BuildTask


from pathlib import Path, PurePath


def default_action(task: BuildTask, config: BuildConfig, prefix: Path):
    for include in IncludeConfig.convert_list(config.target):
        task.plan.glob(
            src=include.source,
            dst=prefix / include.prefix,
            glob="**/*",
            ignore=[],
        )
