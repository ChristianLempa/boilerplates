"""Config package for configuration management.

This package provides the ConfigManager class for managing application configuration,
including defaults, preferences, and library configurations.
"""

from .config_manager import ConfigManager, LibraryConfig

__all__ = ["ConfigManager", "LibraryConfig"]
