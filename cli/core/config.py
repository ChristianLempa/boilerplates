from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from rich.console import Console

from .variables import Variable, VariableSection, VariableCollection

logger = logging.getLogger(__name__)
console = Console()

class ConfigManager:
    """Manages configuration for the CLI application."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file. If None, uses default location.
        """
        if config_path is None:
            # Default to ~/.config/boilerplates/config.yaml
            config_dir = Path.home() / ".config" / "boilerplates"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / "config.yaml"
        else:
            self.config_path = Path(config_path)
        
        # Create default config if it doesn't exist
        if not self.config_path.exists():
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Create a default configuration file."""
        default_config = {
            "defaults": {},
            "preferences": {
                "editor": "vim",
                "output_dir": None,
                "library_paths": []
            }
        }
        self._write_config(default_config)
        logger.info(f"Created default configuration at {self.config_path}")
    
    def _read_config(self) -> Dict[str, Any]:
        """Read configuration from file.
        
        Returns:
            Dictionary containing the configuration.
            
        Raises:
            yaml.YAMLError: If YAML parsing fails.
        """
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            return config
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML configuration: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to read configuration file: {e}")
            raise
    
    def _write_config(self, config: Dict[str, Any]) -> None:
        """Write configuration to file.
        
        Args:
            config: Dictionary containing the configuration to write.
        """
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            logger.debug(f"Configuration written to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to write configuration file: {e}")
            raise
    
    
    def get_config_path(self) -> Path:
        """Get the path to the configuration file.
        
        Returns:
            Path to the configuration file.
        """
        return self.config_path

    def get_defaults(self, module_name: str) -> Dict[str, Any]:
        """Get default variable values for a module.
        
        Returns defaults in a flat format:
        {
            "var_name": "value",
            "var2_name": "value2"
        }
        
        Args:
            module_name: Name of the module
            
        Returns:
            Dictionary of default values (flat key-value pairs)
        """
        config = self._read_config()
        defaults = config.get("defaults", {})
        return defaults.get(module_name, {})
    
    def set_defaults(self, module_name: str, defaults: Dict[str, Any]) -> None:
        """Set default variable values for a module.
        
        Args:
            module_name: Name of the module
            defaults: Dictionary of defaults (flat key-value pairs):
                      {"var_name": "value", "var2_name": "value2"}
        """
        config = self._read_config()
        
        if "defaults" not in config:
            config["defaults"] = {}
        
        config["defaults"][module_name] = defaults
        self._write_config(config)
        logger.info(f"Updated defaults for module '{module_name}'")
    
    def set_default_value(self, module_name: str, var_name: str, value: Any) -> None:
        """Set a single default variable value.
        
        Args:
            module_name: Name of the module
            var_name: Name of the variable
            value: Default value to set
        """
        defaults = self.get_defaults(module_name)
        defaults[var_name] = value
        self.set_defaults(module_name, defaults)
        logger.info(f"Set default for '{module_name}.{var_name}' = '{value}'")
    
    def get_default_value(self, module_name: str, var_name: str) -> Optional[Any]:
        """Get a single default variable value.
        
        Args:
            module_name: Name of the module
            var_name: Name of the variable
            
        Returns:
            Default value or None if not set
        """
        defaults = self.get_defaults(module_name)
        return defaults.get(var_name)
    
    def clear_defaults(self, module_name: str) -> None:
        """Clear all defaults for a module.
        
        Args:
            module_name: Name of the module
        """
        config = self._read_config()
        
        if "defaults" in config and module_name in config["defaults"]:
            del config["defaults"][module_name]
            self._write_config(config)
            logger.info(f"Cleared defaults for module '{module_name}'")

    def get_preference(self, key: str) -> Optional[Any]:
        """Get a user preference value.
        
        Args:
            key: Preference key (e.g., 'editor', 'output_dir', 'library_paths')
            
        Returns:
            Preference value or None if not set
        """
        config = self._read_config()
        preferences = config.get("preferences", {})
        return preferences.get(key)
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set a user preference value.
        
        Args:
            key: Preference key
            value: Preference value
        """
        config = self._read_config()
        
        if "preferences" not in config:
            config["preferences"] = {}
        
        config["preferences"][key] = value
        self._write_config(config)
        logger.info(f"Set preference '{key}' = '{value}'")
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all user preferences.
        
        Returns:
            Dictionary of all preferences
        """
        config = self._read_config()
        return config.get("preferences", {})
