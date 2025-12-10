"""Icon management for consistent CLI display."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar


class IconManager:
    """Centralized icon management system for consistent CLI display.

    This class provides standardized icons for file types, status indicators,
    and UI elements. Icons use Nerd Font glyphs for consistent display.

    Categories:
        - File types: .yaml, .j2, .json, .md, etc.
        - Status: success, warning, error, info, skipped
        - UI elements: folders, config, locks, etc.
    """

    # File Type Icons
    FILE_FOLDER = "\uf07b"
    FILE_DEFAULT = "\uf15b"
    FILE_YAML = "\uf15c"
    FILE_JSON = "\ue60b"
    FILE_MARKDOWN = "\uf48a"
    FILE_JINJA2 = "\ue235"
    FILE_DOCKER = "\uf308"
    FILE_COMPOSE = "\uf308"
    FILE_SHELL = "\uf489"
    FILE_PYTHON = "\ue73c"
    FILE_TEXT = "\uf15c"

    # Status Indicators
    STATUS_SUCCESS = "\uf00c"  #  (check)
    STATUS_ERROR = "\uf00d"  #  (times/x)
    STATUS_WARNING = "\uf071"  #  (exclamation-triangle)
    STATUS_INFO = "\uf05a"  #  (info-circle)
    STATUS_SKIPPED = "\uf05e"  #  (ban/circle-slash)

    # UI Elements
    UI_CONFIG = "\ue5fc"
    UI_LOCK = "\uf084"
    UI_SETTINGS = "\uf013"
    UI_ARROW_RIGHT = "\uf061"  #  (arrow-right)
    UI_BULLET = "\uf111"  #  (circle)
    UI_LIBRARY_GIT = "\uf418"  #  (git icon)
    UI_LIBRARY_STATIC = "\uf07c"  #  (folder icon)

    # Shortcode Mappings (emoji-style codes to Nerd Font icons)
    # Format: ":code:" -> "\uf000"
    #
    # Usage:
    # 1. In regular text: ":mycode: Some text" - icon replaces shortcode inline
    # 2. In markdown lists: "- :mycode: List item" - icon replaces bullet with color
    #
    # To add new shortcodes:
    # 1. Add entry to this dict: ":mycode:": "\uf000"
    # 2. Use in template descriptions or markdown content
    # 3. Shortcodes are automatically replaced when markdown is rendered
    # 4. List items starting with shortcodes get colored icons instead of bullets
    #
    # Find Nerd Font codes at: https://www.nerdfonts.com/cheat-sheet
    SHORTCODES: ClassVar[dict[str, str]] = {
        ":warning:": "\uf071",  #  (exclamation-triangle)
        ":info:": "\uf05a",  #  (info-circle)
        ":check:": "\uf00c",  #  (check)
        ":error:": "\uf00d",  #  (times/x)
        ":lock:": "\uf084",  #  (lock)
        ":folder:": "\uf07b",  #  (folder)
        ":file:": "\uf15b",  #  (file)
        ":gear:": "\uf013",  #  (settings/gear)
        ":rocket:": "\uf135",  #  (rocket)
        ":star:": "\uf005",  #  (star)
        ":lightning:": "\uf0e7",  #  (bolt/lightning)
        ":cloud:": "\uf0c2",  #  (cloud)
        ":database:": "\uf1c0",  #  (database)
        ":network:": "\uf6ff",  #  (network)
        ":docker:": "\uf308",  #  (docker)
        ":kubernetes:": "\ue287",  #  (kubernetes/helm)
    }

    @classmethod
    def get_file_icon(cls, file_path: str | Path) -> str:
        """Get the appropriate icon for a file based on its extension or name.

        Args:
            file_path: Path to the file (can be string or Path object)

        Returns:
            Unicode icon character for the file type

        Examples:
            >>> IconManager.get_file_icon("config.yaml")
            '\uf15c'
            >>> IconManager.get_file_icon("template.j2")
            '\ue235'
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        file_name = file_path.name.lower()
        suffix = file_path.suffix.lower()

        # Check for Docker Compose files
        compose_names = {
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        }
        if file_name in compose_names or file_name.startswith("docker-compose"):
            return cls.FILE_DOCKER

        # Check by extension
        extension_map = {
            ".yaml": cls.FILE_YAML,
            ".yml": cls.FILE_YAML,
            ".json": cls.FILE_JSON,
            ".md": cls.FILE_MARKDOWN,
            ".j2": cls.FILE_JINJA2,
            ".sh": cls.FILE_SHELL,
            ".py": cls.FILE_PYTHON,
            ".txt": cls.FILE_TEXT,
        }

        return extension_map.get(suffix, cls.FILE_DEFAULT)

    @classmethod
    def get_status_icon(cls, status: str) -> str:
        """Get the appropriate icon for a status indicator.

        Args:
            status: Status type (success, error, warning, info, skipped)

        Returns:
            Unicode icon character for the status

        Examples:
            >>> IconManager.get_status_icon("success")
            '✓'
            >>> IconManager.get_status_icon("warning")
            '⚠'
        """
        status_map = {
            "success": cls.STATUS_SUCCESS,
            "error": cls.STATUS_ERROR,
            "warning": cls.STATUS_WARNING,
            "info": cls.STATUS_INFO,
            "skipped": cls.STATUS_SKIPPED,
        }
        return status_map.get(status.lower(), cls.STATUS_INFO)

    @classmethod
    def folder(cls) -> str:
        """Get the folder icon."""
        return cls.FILE_FOLDER

    @classmethod
    def config(cls) -> str:
        """Get the config icon."""
        return cls.UI_CONFIG

    @classmethod
    def lock(cls) -> str:
        """Get the lock icon (for sensitive variables)."""
        return cls.UI_LOCK

    @classmethod
    def arrow_right(cls) -> str:
        """Get the right arrow icon (for showing transitions/changes)."""
        return cls.UI_ARROW_RIGHT

    @classmethod
    def replace_shortcodes(cls, text: str) -> str:
        """Replace emoji-style shortcodes with Nerd Font icons.

        Args:
            text: Text containing shortcodes like :warning:, :info:, etc.

        Returns:
            Text with shortcodes replaced by Nerd Font icons

        Examples:
            >>> IconManager.replace_shortcodes(":warning: This is a warning")
            ' This is a warning'
            >>> IconManager.replace_shortcodes(":docker: :kubernetes: Stack")
            '  Stack'
        """
        result = text
        for shortcode, icon in cls.SHORTCODES.items():
            result = result.replace(shortcode, icon)
        return result
