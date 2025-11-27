"""Display configuration settings for the CLI."""


class DisplaySettings:
    """Centralized display configuration settings.

    This class holds all configurable display parameters including colors,
    styles, layouts, and formatting options. Modify these values to customize
    the CLI appearance.
    """

    # === Color Scheme ===
    COLOR_ERROR = "red"
    COLOR_WARNING = "yellow"
    COLOR_SUCCESS = "green"
    COLOR_INFO = "blue"
    COLOR_MUTED = "dim"

    # Library type colors
    COLOR_LIBRARY_GIT = "blue"
    COLOR_LIBRARY_STATIC = "yellow"

    # === Style Constants ===
    STYLE_HEADER = "bold white underline"
    STYLE_HEADER_ALT = "bold cyan"
    STYLE_DISABLED = "bright_black"
    STYLE_SECTION_TITLE = "bold cyan"
    STYLE_SECTION_DESC = "dim"
    STYLE_TEMPLATE_NAME = "bold white"

    # Table styles
    STYLE_TABLE_HEADER = "bold blue"
    STYLE_VAR_COL_NAME = "white"
    STYLE_VAR_COL_TYPE = "magenta"
    STYLE_VAR_COL_DEFAULT = "green"
    STYLE_VAR_COL_DESC = "white"

    # === Text Labels ===
    LABEL_REQUIRED = " [yellow](*)[/yellow]"
    LABEL_DISABLED = " (disabled)"
    TEXT_EMPTY_VALUE = "(none)"
    TEXT_EMPTY_OVERRIDE = "(empty)"
    TEXT_UNNAMED_TEMPLATE = "Unnamed Template"
    TEXT_NO_DESCRIPTION = "No description available"
    TEXT_VERSION_NOT_SPECIFIED = "Not specified"

    # === Value Formatting ===
    SENSITIVE_MASK = "********"
    TRUNCATION_SUFFIX = "..."
    VALUE_MAX_LENGTH_SHORT = 15
    VALUE_MAX_LENGTH_DEFAULT = 30

    # === Layout Constants ===
    SECTION_SEPARATOR_CHAR = "─"
    SECTION_SEPARATOR_LENGTH = 40
    VAR_NAME_INDENT = "  "  # 2 spaces

    # === Size Formatting ===
    SIZE_KB_THRESHOLD = 1024
    SIZE_MB_THRESHOLD = 1024 * 1024
    SIZE_DECIMAL_PLACES = 1

    # === Table Padding ===
    PADDING_PANEL = (1, 2)
    PADDING_TABLE_COMPACT = (0, 1)
    PADDING_TABLE_NORMAL = (0, 2)
