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
        else:
            # Migrate existing config if needed
            self._migrate_config_if_needed()
    
    def _create_default_config(self) -> None:
        """Create a default configuration file."""
        default_config = {
            "defaults": {},
            "preferences": {
                "editor": "vim",
                "output_dir": None,
                "library_paths": []
            },
            "libraries": [
                {
                    "name": "default",
                    "type": "git",
                    "url": "https://github.com/christianlempa/boilerplates.git",
                    "branch": "main",
                    "directory": "library",
                    "enabled": True
                }
            ]
        }
        self._write_config(default_config)
        logger.info(f"Created default configuration at {self.config_path}")
    
    def _migrate_config_if_needed(self) -> None:
        """Migrate existing config to add missing sections and library types."""
        try:
            config = self._read_config()
            needs_migration = False
            
            # Add libraries section if missing
            if "libraries" not in config:
                logger.info("Migrating config: adding libraries section")
                config["libraries"] = [
                    {
                        "name": "default",
                        "type": "git",
                        "url": "https://github.com/christianlempa/boilerplates.git",
                        "branch": "refactor/boilerplates-v2",
                        "directory": "library",
                        "enabled": True
                    }
                ]
                needs_migration = True
            else:
                # Migrate existing libraries to add 'type' field if missing
                # For backward compatibility, assume all old libraries without 'type' are git libraries
                libraries = config.get("libraries", [])
                for library in libraries:
                    if "type" not in library:
                        logger.info(f"Migrating library '{library.get('name', 'unknown')}': adding type: git")
                        library["type"] = "git"
                        needs_migration = True
            
            # Write back if migration was needed
            if needs_migration:
                self._write_config(config)
                logger.info("Config migration completed successfully")
        except Exception as e:
            logger.warning(f"Config migration failed: {e}")
    
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
        
        # Validate libraries structure
        if "libraries" in config:
            libraries = config["libraries"]
            
            if not isinstance(libraries, list):
                raise ConfigValidationError("'libraries' must be a list")
            
            self._validate_list_length(libraries, "Libraries list")
            
            for i, library in enumerate(libraries):
                if not isinstance(library, dict):
                    raise ConfigValidationError(f"Library at index {i} must be a dictionary")
                
                # Validate name field (required for all library types)
                if "name" not in library:
                    raise ConfigValidationError(f"Library at index {i} missing required field 'name'")
                if not isinstance(library["name"], str):
                    raise ConfigValidationError(f"Library 'name' at index {i} must be a string")
                self._validate_string_length(library["name"], f"Library 'name' at index {i}", max_length=500)
                
                # Validate type field (default to "git" for backward compatibility)
                lib_type = library.get("type", "git")
                if lib_type not in ("git", "static"):
                    raise ConfigValidationError(f"Library type at index {i} must be 'git' or 'static', got '{lib_type}'")
                
                # Type-specific validation
                if lib_type == "git":
                    # Git libraries require: url, directory
                    required_fields = ["url", "directory"]
                    for field in required_fields:
                        if field not in library:
                            raise ConfigValidationError(f"Git library at index {i} missing required field '{field}'")
                        
                        if not isinstance(library[field], str):
                            raise ConfigValidationError(f"Library '{field}' at index {i} must be a string")
                        
                        self._validate_string_length(library[field], f"Library '{field}' at index {i}", max_length=500)
                    
                    # Validate optional branch field
                    if "branch" in library:
                        if not isinstance(library["branch"], str):
                            raise ConfigValidationError(f"Library 'branch' at index {i} must be a string")
                        self._validate_string_length(library["branch"], f"Library 'branch' at index {i}", max_length=200)
                
                elif lib_type == "static":
                    # Static libraries require: path
                    if "path" not in library:
                        raise ConfigValidationError(f"Static library at index {i} missing required field 'path'")
                    
                    if not isinstance(library["path"], str):
                        raise ConfigValidationError(f"Library 'path' at index {i} must be a string")
                    
                    self._validate_path_string(library["path"], f"Library 'path' at index {i}")
                
                # Validate optional enabled field (applies to all types)
                if "enabled" in library and not isinstance(library["enabled"], bool):
                    raise ConfigValidationError(f"Library 'enabled' at index {i} must be a boolean")
    
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
    
    def get_libraries(self) -> list[Dict[str, Any]]:
        """Get all configured libraries.
        
        Returns:
            List of library configurations
        """
        config = self._read_config()
        return config.get("libraries", [])
    
    def get_library_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific library by name.
        
        Args:
            name: Name of the library
            
        Returns:
            Library configuration dictionary or None if not found
        """
        libraries = self.get_libraries()
        for library in libraries:
            if library.get("name") == name:
                return library
        return None
    
    def add_library(
        self,
        name: str,
        library_type: str = "git",
        url: Optional[str] = None,
        directory: Optional[str] = None,
        branch: str = "main",
        path: Optional[str] = None,
        enabled: bool = True
    ) -> None:
        """Add a new library to the configuration.
        
        Args:
            name: Unique name for the library
            library_type: Type of library ("git" or "static")
            url: Git repository URL (required for git type)
            directory: Directory within repo (required for git type)
            branch: Git branch (for git type)
            path: Local path to templates (required for static type)
            enabled: Whether the library is enabled
            
        Raises:
            ConfigValidationError: If library with the same name already exists or validation fails
        """
        # Validate name
        if not isinstance(name, str) or not name:
            raise ConfigValidationError("Library name must be a non-empty string")
        
        self._validate_string_length(name, "Library name", max_length=100)
        
        # Validate type
        if library_type not in ("git", "static"):
            raise ConfigValidationError(f"Library type must be 'git' or 'static', got '{library_type}'")
        
        # Check if library already exists
        if self.get_library_by_name(name):
            raise ConfigValidationError(f"Library '{name}' already exists")
        
        # Type-specific validation and config building
        if library_type == "git":
            if not url:
                raise ConfigValidationError("Git libraries require 'url' parameter")
            if not directory:
                raise ConfigValidationError("Git libraries require 'directory' parameter")
            
            # Validate git-specific fields
            if not isinstance(url, str) or not url:
                raise ConfigValidationError("Library URL must be a non-empty string")
            self._validate_string_length(url, "Library URL", max_length=500)
            
            if not isinstance(directory, str) or not directory:
                raise ConfigValidationError("Library directory must be a non-empty string")
            self._validate_string_length(directory, "Library directory", max_length=200)
            
            if not isinstance(branch, str) or not branch:
                raise ConfigValidationError("Library branch must be a non-empty string")
            self._validate_string_length(branch, "Library branch", max_length=200)
            
            library_config = {
                "name": name,
                "type": "git",
                "url": url,
                "branch": branch,
                "directory": directory,
                "enabled": enabled
            }
        
        else:  # static
            if not path:
                raise ConfigValidationError("Static libraries require 'path' parameter")
            
            # Validate static-specific fields
            if not isinstance(path, str) or not path:
                raise ConfigValidationError("Library path must be a non-empty string")
            self._validate_path_string(path, "Library path")
            
            # For backward compatibility with older CLI versions,
            # add dummy values for git-specific fields
            library_config = {
                "name": name,
                "type": "static",
                "url": "",  # Empty string for backward compatibility
                "branch": "main",  # Default value for backward compatibility
                "directory": ".",  # Default value for backward compatibility
                "path": path,
                "enabled": enabled
            }
        
        config = self._read_config()
        
        if "libraries" not in config:
            config["libraries"] = []
        
        config["libraries"].append(library_config)
        
        self._write_config(config)
        logger.info(f"Added {library_type} library '{name}'")
    
    def remove_library(self, name: str) -> None:
        """Remove a library from the configuration.
        
        Args:
            name: Name of the library to remove
            
        Raises:
            ConfigError: If library is not found
        """
        config = self._read_config()
        libraries = config.get("libraries", [])
        
        # Find and remove the library
        new_libraries = [lib for lib in libraries if lib.get("name") != name]
        
        if len(new_libraries) == len(libraries):
            raise ConfigError(f"Library '{name}' not found")
        
        config["libraries"] = new_libraries
        self._write_config(config)
        logger.info(f"Removed library '{name}'")
    
    def update_library(self, name: str, **kwargs: Any) -> None:
        """Update a library's configuration.
        
        Args:
            name: Name of the library to update
            **kwargs: Fields to update (url, branch, directory, enabled)
            
        Raises:
            ConfigError: If library is not found
            ConfigValidationError: If validation fails
        """
        config = self._read_config()
        libraries = config.get("libraries", [])
        
        # Find the library
        library_found = False
        for library in libraries:
            if library.get("name") == name:
                library_found = True
                
                # Update allowed fields
                if "url" in kwargs:
                    url = kwargs["url"]
                    if not isinstance(url, str) or not url:
                        raise ConfigValidationError("Library URL must be a non-empty string")
                    self._validate_string_length(url, "Library URL", max_length=500)
                    library["url"] = url
                
                if "branch" in kwargs:
                    branch = kwargs["branch"]
                    if not isinstance(branch, str) or not branch:
                        raise ConfigValidationError("Library branch must be a non-empty string")
                    self._validate_string_length(branch, "Library branch", max_length=200)
                    library["branch"] = branch
                
                if "directory" in kwargs:
                    directory = kwargs["directory"]
                    if not isinstance(directory, str) or not directory:
                        raise ConfigValidationError("Library directory must be a non-empty string")
                    self._validate_string_length(directory, "Library directory", max_length=200)
                    library["directory"] = directory
                
                if "enabled" in kwargs:
                    enabled = kwargs["enabled"]
                    if not isinstance(enabled, bool):
                        raise ConfigValidationError("Library enabled must be a boolean")
                    library["enabled"] = enabled
                
                break
        
        if not library_found:
            raise ConfigError(f"Library '{name}' not found")
        
        config["libraries"] = libraries
        self._write_config(config)
        logger.info(f"Updated library '{name}'")
    
    def get_libraries_path(self) -> Path:
        """Get the path to the libraries directory.
        
        Returns:
            Path to the libraries directory (same directory as config file)
        """
        return self.config_path.parent / "libraries"
