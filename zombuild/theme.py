from .console import Style

class Theme:
    HEADING = Style.YELLOW + Style.BOLD
    KEYWORD = Style.WHITE + Style.BOLD
    WARNING = Style.RED + Style.BOLD
    ERROR = Style.RED + Style.BOLD
    TRACE = Style.GRAY
    TRACE_ITALIC = Style.GRAY + Style.ITALIC
