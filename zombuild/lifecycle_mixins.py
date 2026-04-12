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
