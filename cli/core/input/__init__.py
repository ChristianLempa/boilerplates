"""Input management package for CLI user input operations.

This package provides centralized input handling with standardized styling
and validation across the entire CLI application.
"""

from .input_manager import InputManager
from .input_settings import InputSettings

__all__ = ["InputManager", "InputSettings"]
