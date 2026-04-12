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

import re
from argparse import Action
from argparse import ArgumentError
from argparse import ArgumentParser
from argparse import Namespace
from argparse import _ActionsContainer
from argparse import _SubParsersAction
from pathlib import Path
from typing import Any
from typing import Sequence

import colorama

from zombuild import fs
from zombuild._arguments import ZombuildArguments

from ._invocation import Invocation


class DefineAction(Action):
    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        assert isinstance(values, str)
        matched = re.match(r"^([-\w_.]+)\s*[=]\s*(.*)$", values)
        if matched is None:
            raise ArgumentError(self, f"malformed property descriptor: {values}")
        properties = getattr(namespace, "properties", {})
        properties[matched[1]] = matched[2]
        setattr(namespace, "properties", properties)

    pass


def main():
    colorama.just_fix_windows_console()

    #############################

    parser = ArgumentParser(
        prog="zombuild",
        description="build tool for project zomboid mods",
    )

    _set_universal(parser)

    parser.add_argument("-p", "--project", action="store", default=".")

    subparsers = parser.add_subparsers(title="command")

    _define_run(subparsers)
    _define_list(subparsers)

    #############################

    args_namespace = parser.parse_args()
    args = ZombuildArguments(**vars(args_namespace))
    project = fs.expand(args.project, Path.cwd().absolute())
    invocation = Invocation(args, project)
    invocation.execute()


def _set_universal(parser: _ActionsContainer):
    parser.add_argument("-D", "--define", action=DefineAction)
    parser.add_argument("-v", "--verbose", action="count", default=0)


def _define_emitschema(subparsers: _SubParsersAction[ArgumentParser]):
    cmd = subparsers.add_parser("schema")
    cmd.add_argument("which", metavar="task", nargs="1", help="schema to emit")


def _define_run(subparsers: _SubParsersAction[ArgumentParser]):
    cmd = subparsers.add_parser("run")
    cmd.set_defaults(command="run")
    _set_universal(cmd)
    cmd.add_argument("tasks", metavar="task", nargs="*", help="one or more task names")
    cmd.add_argument("-d", "--dry-run", action="store_true")
    cmd.add_argument("-c", "--copy", dest="symlink", action="store_false")
    cmd.add_argument("-w", "--workshop", action="store")


def _define_list(subparsers: _SubParsersAction[ArgumentParser]):
    cmd = subparsers.add_parser("list", description="list all tasks")
    _set_universal(cmd)
    cmd.set_defaults(command="list")
    cmd.add_argument("-t", "--types", dest="list_types", action="store_true")


if __name__ == "__main__":
    main()
