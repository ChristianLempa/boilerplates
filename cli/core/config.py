"""
Configuration management for the Boilerplates CLI.
Handles module-specific configuration stored in config.json files.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .logging import setup_logging


class ConfigManager:
    """Manages configuration for CLI modules."""

    def __init__(self, module_name: str):
        self.module_name = module_name
        self.config_dir = Path.home() / ".boilerplates"
        self.config_file = self.config_dir / f"{module_name}.json"
        self.logger = setup_logging()

    def _ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self.logger.warning(f"Failed to load config for {self.module_name}: {e}")
            return {}

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        self._ensure_config_dir()
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            self.logger.error(f"Failed to save config for {self.module_name}: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        config = self._load_config()
        return config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        config = self._load_config()
        config[key] = value
        self._save_config(config)

    def delete(self, key: str) -> bool:
        """Delete a configuration value."""
        config = self._load_config()
        if key in config:
            del config[key]
            self._save_config(config)
            return True
        return False

    def list_all(self) -> Dict[str, Any]:
        """List all configuration values."""
        return self._load_config()

    def get_config_path(self) -> Path:
        """Get the path to the configuration file."""
        return self.config_file
