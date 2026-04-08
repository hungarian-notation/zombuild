import sys
import traceback
from pydantic import ValidationError
from zombuild.console import Indent, Style, Text
from zombuild.theme import Theme


class ZombuildException(Exception):
    pass


class ZombuildConfigException(ZombuildException):

    def __init__(self, *args: object, validation_error: ValidationError) -> None:
        super().__init__(*args)

        self.validation_error = validation_error


def _format_traceback(e: Exception):
    if e.__traceback__ is not None:
        print()

        for frame in traceback.extract_tb(e.__traceback__):
            t1 = Text(frame.filename, Theme.TRACE_ITALIC)
            t2 = Text(f"line {frame.lineno}", Theme.TRACE)
            print(Indent(t1 + " " + t2, 2))
        print()


def _format_notes(e: BaseException):
    for note in e.__notes__:
        t1 = Text(note, Theme.TRACE)
        print(Indent(t1, 2))


def unhandled_exception_reporter(e: Exception):
    if isinstance(e, ZombuildConfigException):
        _format_traceback(e)
        print(Text(f"Config Error:", Theme.ERROR), end=" ")
        print(e.validation_error.title)
        print()

        errors = e.validation_error.errors(include_url=False)

        for details in errors:
            location_array = details.get("loc")

            if location_array is not None:
                location = Text(".".join(map(str, location_array[:-1])), Theme.KEYWORD)
                location_type = Text(location_array[-1:][0])

                print(Indent(location + " " + location_type, 2))
                print(Indent(details.get("msg"), 4))
            else:
                print(Indent(details.get("msg"), 2))
            print()

        if hasattr(e, "__notes__") and e.__notes__:
            _format_notes(e)
            print()
        sys.exit(1)

    if isinstance(e, ZombuildException):
        _format_traceback(e)
        print(Text(f"Build Error:", Theme.ERROR), end=" ")
        print(e)
        if hasattr(e, "__notes__") and e.__notes__:
            print()
            _format_notes(e)
        sys.exit(1)
    else:
        _format_traceback(e)
        print(Text(f"Unhandled {e.__class__.__name__}:", Theme.ERROR), end=" ")
        print(e)
        if hasattr(e, "__notes__") and e.__notes__:
            print()
            _format_notes(e)
        sys.exit(1)
