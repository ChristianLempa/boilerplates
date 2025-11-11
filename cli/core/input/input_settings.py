"""Input configuration settings for the CLI.

This module defines all configurable input parameters including prompt styles,
colors, and default behaviors.
"""


class InputSettings:
    """Centralized input configuration settings.

    This class holds all configurable input parameters including prompt styles,
    colors, validation messages, and default behaviors.
    """

    # === Prompt Styles ===
    PROMPT_STYLE = "white"
    PROMPT_DEFAULT_STYLE = "dim"
    PROMPT_ERROR_STYLE = "red"
    PROMPT_SUCCESS_STYLE = "green"

    # === Validation Messages ===
    MSG_INVALID_INTEGER = "Please enter a valid integer"
    MSG_INVALID_FLOAT = "Please enter a valid number"
    MSG_INVALID_EMAIL = "Please enter a valid email address"
    MSG_INVALID_URL = "Please enter a valid URL"
    MSG_INVALID_HOSTNAME = "Please enter a valid hostname"
    MSG_REQUIRED = "This field is required"
    MSG_INVALID_CHOICE = "Please select a valid option"

    # === Default Values ===
    DEFAULT_CONFIRM_YES = True
    DEFAULT_PASSWORD_MASK = "•"

    # === Prompt Labels ===
    LABEL_DEFAULT = "default"
    LABEL_AUTO = "*auto"
    LABEL_OPTIONAL = "optional"
