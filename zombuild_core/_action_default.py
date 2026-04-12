# Zombuild
# Copyright (C) 2026 Chris Bode and Zombuild Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from pathlib import Path
from pathlib import PurePath

from zombuild.config.include import BuildConfig
from zombuild.config.include import IncludeConfig
from zombuild_core.BuildTask import BuildTask


def default_action(task: BuildTask, config: BuildConfig, prefix: Path):
    for include in IncludeConfig.convert_list(config.target):
        task.plan.glob(
            src=include.source,
            dst=prefix / include.prefix,
            glob="**/*",
            ignore=[],
        )
