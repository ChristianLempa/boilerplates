"""Config package for configuration management.

This package provides the ConfigManager class for managing application configuration,
including defaults, preferences, and library configurations.
"""

from .config_manager import ConfigManager, LibraryConfig, is_legacy_default_library_url, normalize_git_url

__all__ = ["ConfigManager", "LibraryConfig", "is_legacy_default_library_url", "normalize_git_url"]
