"""Icon management for consistent CLI display."""

from __future__ import annotations

from pathlib import Path


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
    FILE_FOLDER = "\uf07b"  #
    FILE_DEFAULT = "\uf15b"  #
    FILE_YAML = "\uf15c"  #
    FILE_JSON = "\ue60b"  #
    FILE_MARKDOWN = "\uf48a"  #
    FILE_JINJA2 = "\ue235"  #
    FILE_DOCKER = "\uf308"  #
    FILE_COMPOSE = "\uf308"  #
    FILE_SHELL = "\uf489"  #
    FILE_PYTHON = "\ue73c"  #
    FILE_TEXT = "\uf15c"  #

    # Status Indicators
    STATUS_SUCCESS = "\uf00c"  #  (check)
    STATUS_ERROR = "\uf00d"  #  (times/x)
    STATUS_WARNING = "\uf071"  #  (exclamation-triangle)
    STATUS_INFO = "\uf05a"  #  (info-circle)
    STATUS_SKIPPED = "\uf05e"  #  (ban/circle-slash)

    # UI Elements
    UI_CONFIG = "\ue5fc"  #
    UI_LOCK = "\uf084"  #
    UI_SETTINGS = "\uf013"  #
    UI_ARROW_RIGHT = "\uf061"  #  (arrow-right)
    UI_BULLET = "\uf111"  #  (circle)
    UI_LIBRARY_GIT = "\uf418"  #  (git icon)
    UI_LIBRARY_STATIC = "\uf07c"  #  (folder icon)

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
