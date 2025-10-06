from __future__ import annotations

import logging
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from rich.console import Console

from .variables import Variable, VariableSection, VariableCollection

logger = logging.getLogger(__name__)
console = Console()

# Valid Python identifier pattern for variable names
VALID_IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

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
            ValueError: If configuration structure is invalid.
        """
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            # Validate config structure
            self._validate_config_structure(config)
            
            return config
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML configuration: {e}")
            raise
        except ValueError as e:
            logger.error(f"Invalid configuration structure: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to read configuration file: {e}")
            raise
    
    def _write_config(self, config: Dict[str, Any]) -> None:
        """Write configuration to file atomically using temp file + rename pattern.
        
        This prevents config file corruption if write operation fails partway through.
        
        Args:
            config: Dictionary containing the configuration to write.
            
        Raises:
            ValueError: If configuration structure is invalid.
        """
        try:
            # Validate config structure before writing
            self._validate_config_structure(config)
            
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temporary file in same directory for atomic rename
            with tempfile.NamedTemporaryFile(
                mode='w',
                delete=False,
                dir=self.config_path.parent,
                prefix='.config_',
                suffix='.tmp'
            ) as tmp_file:
                yaml.dump(config, tmp_file, default_flow_style=False)
                tmp_path = tmp_file.name
            
            # Atomic rename (overwrites existing file on POSIX systems)
            shutil.move(tmp_path, self.config_path)
            logger.debug(f"Configuration written atomically to {self.config_path}")
            
        except ValueError as e:
            logger.error(f"Invalid configuration structure: {e}")
            raise
        except Exception as e:
            # Clean up temp file if it exists
            if 'tmp_path' in locals():
                try:
                    Path(tmp_path).unlink(missing_ok=True)
                except Exception:
                    pass
            logger.error(f"Failed to write configuration file: {e}")
            raise
    
    def _validate_config_structure(self, config: Dict[str, Any]) -> None:
        """Validate the configuration structure.
        
        Args:
            config: Configuration dictionary to validate.
            
        Raises:
            ValueError: If configuration structure is invalid.
        """
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")
        
        # Check top-level structure
        if "defaults" in config and not isinstance(config["defaults"], dict):
            raise ValueError("'defaults' must be a dictionary")
        
        if "preferences" in config and not isinstance(config["preferences"], dict):
            raise ValueError("'preferences' must be a dictionary")
        
        # Validate defaults structure
        if "defaults" in config:
            for module_name, module_defaults in config["defaults"].items():
                if not isinstance(module_name, str):
                    raise ValueError(f"Module name must be a string, got {type(module_name).__name__}")
                
                if not isinstance(module_defaults, dict):
                    raise ValueError(f"Defaults for module '{module_name}' must be a dictionary")
                
                # Validate variable names are valid Python identifiers
                for var_name in module_defaults.keys():
                    if not isinstance(var_name, str):
                        raise ValueError(f"Variable name must be a string, got {type(var_name).__name__}")
                    
                    if not VALID_IDENTIFIER_PATTERN.match(var_name):
                        raise ValueError(
                            f"Invalid variable name '{var_name}' in module '{module_name}'. "
                            f"Variable names must be valid Python identifiers (letters, numbers, underscores, "
                            f"cannot start with a number)"
                        )
        
        # Validate preferences structure and types
        if "preferences" in config:
            preferences = config["preferences"]
            
            # Validate known preference types
            if "editor" in preferences and not isinstance(preferences["editor"], str):
                raise ValueError("Preference 'editor' must be a string")
            
            if "output_dir" in preferences:
                if preferences["output_dir"] is not None and not isinstance(preferences["output_dir"], str):
                    raise ValueError("Preference 'output_dir' must be a string or null")
            
            if "library_paths" in preferences:
                if not isinstance(preferences["library_paths"], list):
                    raise ValueError("Preference 'library_paths' must be a list")
                
                for path in preferences["library_paths"]:
                    if not isinstance(path, str):
                        raise ValueError(f"Library path must be a string, got {type(path).__name__}")
    
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
                      
        Raises:
            ValueError: If module name or variable names are invalid.
        """
        # Validate module name
        if not isinstance(module_name, str) or not module_name:
            raise ValueError("Module name must be a non-empty string")
        
        # Validate defaults dictionary
        if not isinstance(defaults, dict):
            raise ValueError("Defaults must be a dictionary")
        
        # Validate variable names
        for var_name in defaults.keys():
            if not isinstance(var_name, str):
                raise ValueError(f"Variable name must be a string, got {type(var_name).__name__}")
            
            if not VALID_IDENTIFIER_PATTERN.match(var_name):
                raise ValueError(
                    f"Invalid variable name '{var_name}'. Variable names must be valid Python identifiers "
                    f"(letters, numbers, underscores, cannot start with a number)"
                )
        
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
            
        Raises:
            ValueError: If module name or variable name is invalid.
        """
        # Validate inputs
        if not isinstance(module_name, str) or not module_name:
            raise ValueError("Module name must be a non-empty string")
        
        if not isinstance(var_name, str):
            raise ValueError(f"Variable name must be a string, got {type(var_name).__name__}")
        
        if not VALID_IDENTIFIER_PATTERN.match(var_name):
            raise ValueError(
                f"Invalid variable name '{var_name}'. Variable names must be valid Python identifiers "
                f"(letters, numbers, underscores, cannot start with a number)"
            )
        
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
            
        Raises:
            ValueError: If key or value is invalid for known preference types.
        """
        # Validate key
        if not isinstance(key, str) or not key:
            raise ValueError("Preference key must be a non-empty string")
        
        # Validate known preference types
        if key == "editor" and not isinstance(value, str):
            raise ValueError("Preference 'editor' must be a string")
        
        if key == "output_dir":
            if value is not None and not isinstance(value, str):
                raise ValueError("Preference 'output_dir' must be a string or null")
        
        if key == "library_paths":
            if not isinstance(value, list):
                raise ValueError("Preference 'library_paths' must be a list")
            for path in value:
                if not isinstance(path, str):
                    raise ValueError(f"Library path must be a string, got {type(path).__name__}")
        
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
