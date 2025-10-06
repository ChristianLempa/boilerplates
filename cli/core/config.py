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

from .variable import Variable
from .section import VariableSection
from .collection import VariableCollection
from .exceptions import ConfigError, ConfigValidationError, YAMLParseError

logger = logging.getLogger(__name__)
console = Console()

# Valid Python identifier pattern for variable names
VALID_IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

# Valid path pattern - prevents path traversal attempts
VALID_PATH_PATTERN = re.compile(r'^[^\x00-\x1f<>:"|?*]+$')

# Maximum allowed string lengths to prevent DOS attacks
MAX_STRING_LENGTH = 1000
MAX_PATH_LENGTH = 4096
MAX_LIST_LENGTH = 100

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
    
    @staticmethod
    def _validate_string_length(value: str, field_name: str, max_length: int = MAX_STRING_LENGTH) -> None:
        """Validate string length to prevent DOS attacks.
        
        Args:
            value: String value to validate
            field_name: Name of the field for error messages
            max_length: Maximum allowed length
            
        Raises:
            ConfigValidationError: If string exceeds maximum length
        """
        if len(value) > max_length:
            raise ConfigValidationError(
                f"{field_name} exceeds maximum length of {max_length} characters "
                f"(got {len(value)} characters)"
            )
    
    @staticmethod
    def _validate_path_string(path: str, field_name: str) -> None:
        """Validate path string for security concerns.
        
        Args:
            path: Path string to validate
            field_name: Name of the field for error messages
            
        Raises:
            ConfigValidationError: If path contains invalid characters or patterns
        """
        # Check length
        if len(path) > MAX_PATH_LENGTH:
            raise ConfigValidationError(
                f"{field_name} exceeds maximum path length of {MAX_PATH_LENGTH} characters"
            )
        
        # Check for null bytes and control characters
        if '\x00' in path or any(ord(c) < 32 for c in path if c not in '\t\n\r'):
            raise ConfigValidationError(
                f"{field_name} contains invalid control characters"
            )
        
        # Check for path traversal attempts
        if '..' in path.split('/'):
            logger.warning(f"Path '{path}' contains '..' - potential path traversal attempt")
    
    @staticmethod
    def _validate_list_length(lst: list, field_name: str, max_length: int = MAX_LIST_LENGTH) -> None:
        """Validate list length to prevent DOS attacks.
        
        Args:
            lst: List to validate
            field_name: Name of the field for error messages
            max_length: Maximum allowed length
            
        Raises:
            ConfigValidationError: If list exceeds maximum length
        """
        if len(lst) > max_length:
            raise ConfigValidationError(
                f"{field_name} exceeds maximum length of {max_length} items (got {len(lst)} items)"
            )
    
    def _read_config(self) -> Dict[str, Any]:
        """Read configuration from file.
        
        Returns:
            Dictionary containing the configuration.
            
        Raises:
            YAMLParseError: If YAML parsing fails.
            ConfigValidationError: If configuration structure is invalid.
            ConfigError: If reading fails for other reasons.
        """
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            # Validate config structure
            self._validate_config_structure(config)
            
            return config
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML configuration: {e}")
            raise YAMLParseError(str(self.config_path), e)
        except ConfigValidationError:
            # Re-raise validation errors as-is
            raise
        except (IOError, OSError) as e:
            logger.error(f"Failed to read configuration file: {e}")
            raise ConfigError(f"Failed to read configuration file '{self.config_path}': {e}")
    
    def _write_config(self, config: Dict[str, Any]) -> None:
        """Write configuration to file atomically using temp file + rename pattern.
        
        This prevents config file corruption if write operation fails partway through.
        
        Args:
            config: Dictionary containing the configuration to write.
            
        Raises:
            ConfigValidationError: If configuration structure is invalid.
            ConfigError: If writing fails for any reason.
        """
        tmp_path = None
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
            
        except ConfigValidationError:
            # Re-raise validation errors as-is
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)
            raise
        except (IOError, OSError, yaml.YAMLError) as e:
            # Clean up temp file if it exists
            if tmp_path:
                try:
                    Path(tmp_path).unlink(missing_ok=True)
                except (IOError, OSError):
                    logger.warning(f"Failed to clean up temporary file: {tmp_path}")
            logger.error(f"Failed to write configuration file: {e}")
            raise ConfigError(f"Failed to write configuration to '{self.config_path}': {e}")
    
    def _validate_config_structure(self, config: Dict[str, Any]) -> None:
        """Validate the configuration structure with comprehensive checks.
        
        Args:
            config: Configuration dictionary to validate.
            
        Raises:
            ConfigValidationError: If configuration structure is invalid.
        """
        if not isinstance(config, dict):
            raise ConfigValidationError("Configuration must be a dictionary")
        
        # Check top-level structure
        if "defaults" in config and not isinstance(config["defaults"], dict):
            raise ConfigValidationError("'defaults' must be a dictionary")
        
        if "preferences" in config and not isinstance(config["preferences"], dict):
            raise ConfigValidationError("'preferences' must be a dictionary")
        
        # Validate defaults structure
        if "defaults" in config:
            for module_name, module_defaults in config["defaults"].items():
                if not isinstance(module_name, str):
                    raise ConfigValidationError(f"Module name must be a string, got {type(module_name).__name__}")
                
                # Validate module name length
                self._validate_string_length(module_name, "Module name", max_length=100)
                
                if not isinstance(module_defaults, dict):
                    raise ConfigValidationError(f"Defaults for module '{module_name}' must be a dictionary")
                
                # Validate number of defaults per module
                self._validate_list_length(
                    list(module_defaults.keys()), 
                    f"Defaults for module '{module_name}'"
                )
                
                # Validate variable names are valid Python identifiers
                for var_name, var_value in module_defaults.items():
                    if not isinstance(var_name, str):
                        raise ConfigValidationError(f"Variable name must be a string, got {type(var_name).__name__}")
                    
                    # Validate variable name length
                    self._validate_string_length(var_name, "Variable name", max_length=100)
                    
                    if not VALID_IDENTIFIER_PATTERN.match(var_name):
                        raise ConfigValidationError(
                            f"Invalid variable name '{var_name}' in module '{module_name}'. "
                            f"Variable names must be valid Python identifiers (letters, numbers, underscores, "
                            f"cannot start with a number)"
                        )
                    
                    # Validate variable value types and lengths
                    if isinstance(var_value, str):
                        self._validate_string_length(
                            var_value, 
                            f"Value for '{module_name}.{var_name}'"
                        )
                    elif isinstance(var_value, list):
                        self._validate_list_length(
                            var_value, 
                            f"Value for '{module_name}.{var_name}'"
                        )
                    elif var_value is not None and not isinstance(var_value, (bool, int, float)):
                        raise ConfigValidationError(
                            f"Invalid value type for '{module_name}.{var_name}': "
                            f"must be string, number, boolean, list, or null (got {type(var_value).__name__})"
                        )
        
        # Validate preferences structure and types
        if "preferences" in config:
            preferences = config["preferences"]
            
            # Validate known preference types
            if "editor" in preferences:
                if not isinstance(preferences["editor"], str):
                    raise ConfigValidationError("Preference 'editor' must be a string")
                self._validate_string_length(preferences["editor"], "Preference 'editor'", max_length=100)
            
            if "output_dir" in preferences:
                output_dir = preferences["output_dir"]
                if output_dir is not None:
                    if not isinstance(output_dir, str):
                        raise ConfigValidationError("Preference 'output_dir' must be a string or null")
                    self._validate_path_string(output_dir, "Preference 'output_dir'")
            
            if "library_paths" in preferences:
                if not isinstance(preferences["library_paths"], list):
                    raise ConfigValidationError("Preference 'library_paths' must be a list")
                
                self._validate_list_length(preferences["library_paths"], "Preference 'library_paths'")
                
                for i, path in enumerate(preferences["library_paths"]):
                    if not isinstance(path, str):
                        raise ConfigValidationError(f"Library path must be a string, got {type(path).__name__}")
                    self._validate_path_string(path, f"Library path at index {i}")
    
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
        """Set default variable values for a module with comprehensive validation.
        
        Args:
            module_name: Name of the module
            defaults: Dictionary of defaults (flat key-value pairs):
                      {"var_name": "value", "var2_name": "value2"}
                      
        Raises:
            ConfigValidationError: If module name or variable names are invalid.
        """
        # Validate module name
        if not isinstance(module_name, str) or not module_name:
            raise ConfigValidationError("Module name must be a non-empty string")
        
        self._validate_string_length(module_name, "Module name", max_length=100)
        
        # Validate defaults dictionary
        if not isinstance(defaults, dict):
            raise ConfigValidationError("Defaults must be a dictionary")
        
        # Validate number of defaults
        self._validate_list_length(list(defaults.keys()), "Defaults dictionary")
        
        # Validate variable names and values
        for var_name, var_value in defaults.items():
            if not isinstance(var_name, str):
                raise ConfigValidationError(f"Variable name must be a string, got {type(var_name).__name__}")
            
            self._validate_string_length(var_name, "Variable name", max_length=100)
            
            if not VALID_IDENTIFIER_PATTERN.match(var_name):
                raise ConfigValidationError(
                    f"Invalid variable name '{var_name}'. Variable names must be valid Python identifiers "
                    f"(letters, numbers, underscores, cannot start with a number)"
                )
            
            # Validate value types and lengths
            if isinstance(var_value, str):
                self._validate_string_length(var_value, f"Value for '{var_name}'")
            elif isinstance(var_value, list):
                self._validate_list_length(var_value, f"Value for '{var_name}'")
            elif var_value is not None and not isinstance(var_value, (bool, int, float)):
                raise ConfigValidationError(
                    f"Invalid value type for '{var_name}': "
                    f"must be string, number, boolean, list, or null (got {type(var_value).__name__})"
                )
        
        config = self._read_config()
        
        if "defaults" not in config:
            config["defaults"] = {}
        
        config["defaults"][module_name] = defaults
        self._write_config(config)
        logger.info(f"Updated defaults for module '{module_name}'")
    
    def set_default_value(self, module_name: str, var_name: str, value: Any) -> None:
        """Set a single default variable value with comprehensive validation.
        
        Args:
            module_name: Name of the module
            var_name: Name of the variable
            value: Default value to set
            
        Raises:
            ConfigValidationError: If module name or variable name is invalid.
        """
        # Validate inputs
        if not isinstance(module_name, str) or not module_name:
            raise ConfigValidationError("Module name must be a non-empty string")
        
        self._validate_string_length(module_name, "Module name", max_length=100)
        
        if not isinstance(var_name, str):
            raise ConfigValidationError(f"Variable name must be a string, got {type(var_name).__name__}")
        
        self._validate_string_length(var_name, "Variable name", max_length=100)
        
        if not VALID_IDENTIFIER_PATTERN.match(var_name):
            raise ConfigValidationError(
                f"Invalid variable name '{var_name}'. Variable names must be valid Python identifiers "
                f"(letters, numbers, underscores, cannot start with a number)"
            )
        
        # Validate value type and length
        if isinstance(value, str):
            self._validate_string_length(value, f"Value for '{var_name}'")
        elif isinstance(value, list):
            self._validate_list_length(value, f"Value for '{var_name}'")
        elif value is not None and not isinstance(value, (bool, int, float)):
            raise ConfigValidationError(
                f"Invalid value type for '{var_name}': "
                f"must be string, number, boolean, list, or null (got {type(value).__name__})"
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
        """Set a user preference value with comprehensive validation.
        
        Args:
            key: Preference key
            value: Preference value
            
        Raises:
            ConfigValidationError: If key or value is invalid for known preference types.
        """
        # Validate key
        if not isinstance(key, str) or not key:
            raise ConfigValidationError("Preference key must be a non-empty string")
        
        self._validate_string_length(key, "Preference key", max_length=100)
        
        # Validate known preference types
        if key == "editor":
            if not isinstance(value, str):
                raise ConfigValidationError("Preference 'editor' must be a string")
            self._validate_string_length(value, "Preference 'editor'", max_length=100)
        
        elif key == "output_dir":
            if value is not None:
                if not isinstance(value, str):
                    raise ConfigValidationError("Preference 'output_dir' must be a string or null")
                self._validate_path_string(value, "Preference 'output_dir'")
        
        elif key == "library_paths":
            if not isinstance(value, list):
                raise ConfigValidationError("Preference 'library_paths' must be a list")
            
            self._validate_list_length(value, "Preference 'library_paths'")
            
            for i, path in enumerate(value):
                if not isinstance(path, str):
                    raise ConfigValidationError(f"Library path must be a string, got {type(path).__name__}")
                self._validate_path_string(path, f"Library path at index {i}")
        
        # For unknown preference keys, apply basic validation
        else:
            if isinstance(value, str):
                self._validate_string_length(value, f"Preference '{key}'")
            elif isinstance(value, list):
                self._validate_list_length(value, f"Preference '{key}'")
        
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
