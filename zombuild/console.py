"""
Provides a API somewhat like the `rich` library, but without including any dependencies beyond
colorama which is already a transient dependency via pydantic.
"""

import os
import shutil
import textwrap
from typing import TYPE_CHECKING, Iterable, Literal, overload
from colorama import just_fix_windows_console

just_fix_windows_console()

if TYPE_CHECKING:
    from _typeshed import SupportsWrite

type AnsiCodeType = str | int


class Esc:
    ESC = "\x1b"
    BEL = "\x07"
    CSI = {"prefix": "[", "esc": ESC}

    def __init__(
        self,
        *values: AnsiCodeType,
        suffix="",
        prefix="[",
        sep=";",
        esc="\x1b",
    ) -> None:
        converted: list[str] = []

        for v in values:
            if isinstance(v, int):
                converted.append(f"{v:d}")
            else:
                converted.append(v)

        self._codes = converted
        self._esc = esc
        self._sep = sep
        self._prefix = prefix
        self._suffix = suffix

    def __str__(self) -> str:
        return f"{self._esc}{self._prefix}{self._sep.join(self._codes)}{self._suffix}"

    def join(self, other: Esc):
        assert self.is_joinable(other)
        return Esc(
            *self._codes,
            *other._codes,
            suffix=self._suffix,
            prefix=self._prefix,
            sep=self._sep,
            esc=self._esc,
        )

    def __add__(self, other) -> Esc:
        if isinstance(other, Esc) and self.is_joinable(other):
            return self.join(other)
        else:
            raise Exception(f"not joinable: {repr(self)} and {repr(other)}")

    def __iadd__(self, other):
        if isinstance(other, Esc) and self.is_joinable(other):
            return self.join(other)
        else:
            raise ValueError(
                f"can not merge other={repr(other)} {type(other)} into {repr(self)}"
            )

    def is_joinable(self, other: Esc):
        return self.is_graphics() and other.is_graphics()

    def is_graphics(self):
        return (
            self._sep == ";"
            and self._suffix == "m"
            and self._esc == self.ESC
            and self._prefix == "["
        )

    @classmethod
    def gfx(cls, *codes: AnsiCodeType):
        return Esc(*codes, suffix="m", **cls.CSI)


# fmt: off
class Style:
    RESET               = Esc.gfx(0)
    BOLD                = Esc.gfx(1)
    DIM                 = Esc.gfx(2)
    ITALIC              = Esc.gfx(3)
    UNDERLINE           = Esc.gfx(4)

    BLACK               = Esc.gfx(30)
    RED                 = Esc.gfx(31)
    GREEN               = Esc.gfx(32)
    YELLOW              = Esc.gfx(33)
    BLUE                = Esc.gfx(34)
    MAGENTA             = Esc.gfx(35)
    CYAN                = Esc.gfx(36)
    WHITE               = Esc.gfx(37)
    DEFAULT             = Esc.gfx(39)    

    BRIGHT_BLACK        = Esc.gfx(90) 
    GRAY                = Esc.gfx(90)

    BRIGHT_RED          = Esc.gfx(91)
    BRIGHT_GREEN        = Esc.gfx(92)
    BRIGHT_YELLOW       = Esc.gfx(93)
    BRIGHT_BLUE         = Esc.gfx(94)
    BRIGHT_MAGENTA      = Esc.gfx(95)
    BRIGHT_CYAN         = Esc.gfx(96)
    BRIGHT_WHITE        = Esc.gfx(97)

    BG_BLACK            = Esc.gfx(40)
    BG_RED              = Esc.gfx(41)
    BG_GREEN            = Esc.gfx(42)
    BG_YELLOW           = Esc.gfx(43)
    BG_BLUE             = Esc.gfx(44)
    BG_MAGENTA          = Esc.gfx(45)
    BG_CYAN             = Esc.gfx(46)
    BG_WHITE            = Esc.gfx(47)
    BG_DEFAULT          = Esc.gfx(49)

    BG_BRIGHT_BLACK     = Esc.gfx(100)
    BG_BRIGHT_RED       = Esc.gfx(101)
    BG_BRIGHT_GREEN     = Esc.gfx(102)
    BG_BRIGHT_YELLOW    = Esc.gfx(103)
    BG_BRIGHT_BLUE      = Esc.gfx(104)
    BG_BRIGHT_MAGENTA   = Esc.gfx(105)
    BG_BRIGHT_CYAN      = Esc.gfx(106)
    BG_BRIGHT_WHITE     = Esc.gfx(107)
# fmt: on


class Console:

    def print(
        self,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        file: SupportsWrite[str] | None = None,
        flush: Literal[False] = False,
    ):
        strings = list(map(str, values))
        print(*strings, sep=sep, end=end, file=file, flush=flush)


type _CommonWhitespace = Literal[
    "\t",
    "\t\t",
    "\t\t\t",
    "\t\t\t\t",
    "\r",
    "\n",
    "\n\n",
    "\n\n\n",
    "\r\n",
    "\r\n\r\n",
    "\r\n\r\n\r\n",
    " ",
    "  ",
    "   ",
    "    ",
    "     ",
    "      ",
    "       ",
    "        ",
]
"""
    Hackish attempt to allow the Text __add__ overloads to hint that it always returns a Text 
    instance when added with a whitespace string.
"""


class Text:

    _unstyled = ("", str(Style.RESET))

    def __init__(
        self, value: object = "", style: str | Esc | Style = Style.RESET
    ) -> None:
        self._style = style
        self._strings: list[str] = []

        if value != "":
            self.append(str(value))

    def append(self, value: str):
        self._strings.append(value)

    def extend(self, values: Iterable[str]):
        for v in values:
            self.append(v)

    def __str__(self) -> str:
        style = str(self._style)
        reset = "" if style in self._unstyled else Style.RESET
        return f"{self._style}{"".join(self._strings)}{reset}"

    @overload
    def __add__(self, other: _CommonWhitespace) -> Text: ...
    @overload
    def __add__(self, other: Text | str) -> str | Text: ...

    def __add__(self, other: Text | str) -> str | Text:

        if isinstance(other, Text) and other._style == self._style:
            new = Text("", self._style)
            new.extend(self._strings)
            new.extend(other._strings)
            return new

        if isinstance(other, str):
            if self._style in self._unstyled or other.isspace():
                new = Text("", self._style)
                new.extend(self._strings)
                new.append(other)
                return new

        return str(self) + str(other)

    @classmethod
    def assemble(cls, *values: object):
        t = Text()
        for v in values:
            t.append(str(v))
        return t


class Indent:

    def __init__(self, renderable: str | Text | object, indent: str | int = 4) -> None:
        self._content = renderable
        self._indent = (" " * indent) if isinstance(indent, int) else str(indent)

    def __str__(self) -> str:
        columns = shutil.get_terminal_size().columns
        content = str(self._content)
        indent = self._indent
        return os.linesep.join(
            textwrap.wrap(
                content, columns, initial_indent=indent, subsequent_indent=indent
            )
        )
