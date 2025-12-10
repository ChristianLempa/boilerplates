from __future__ import annotations

import logging
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..exceptions import ConfigError, ConfigValidationError, YAMLParseError

logger = logging.getLogger(__name__)


@dataclass
class LibraryConfig:
    """Configuration for a template library."""

    name: str
    library_type: str = "git"
    url: str | None = None
    directory: str | None = None
    branch: str = "main"
    path: str | None = None
    enabled: bool = True


class ConfigManager:
    """Manages configuration for the CLI application."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        """Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file. If None, auto-detects:
                        1. Checks for ./config.yaml (local project config)
                        2. Falls back to ~/.config/boilerplates/config.yaml (global config)
        """
        if config_path is None:
            # Check for local config.yaml in current directory first
            local_config = Path.cwd() / "config.yaml"
            if local_config.exists() and local_config.is_file():
                self.config_path = local_config
                self.is_local = True
                logger.debug(f"Using local config: {local_config}")
            else:
                # Fall back to global config
                config_dir = Path.home() / ".config" / "boilerplates"
                config_dir.mkdir(parents=True, exist_ok=True)
                self.config_path = config_dir / "config.yaml"
                self.is_local = False
        else:
            self.config_path = Path(config_path)
            self.is_local = False

        # Create default config if it doesn't exist (only for global config)
        if not self.config_path.exists():
            if not self.is_local:
                self._create_default_config()
            else:
                raise ConfigError(f"Local config file not found: {self.config_path}")
        else:
            # Migrate existing config if needed
            self._migrate_config_if_needed()

    def _create_default_config(self) -> None:
        """Create a default configuration file."""
        default_config = {
            "defaults": {},
            "preferences": {"editor": "vim", "output_dir": None, "library_paths": []},
            "libraries": [
                {
                    "name": "default",
                    "type": "git",
                    "url": "https://github.com/christianlempa/boilerplates.git",
                    "branch": "main",
                    "directory": "library",
                    "enabled": True,
                }
            ],
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
                        "enabled": True,
                    }
                ]
                needs_migration = True
            else:
                # Migrate existing libraries to add 'type' field if missing
                # For backward compatibility, assume all old libraries without
                # 'type' are git libraries
                libraries = config.get("libraries", [])
                for library in libraries:
                    if "type" not in library:
                        lib_name = library.get("name", "unknown")
                        logger.info(f"Migrating library '{lib_name}': adding type: git")
                        library["type"] = "git"
                        needs_migration = True

            # Write back if migration was needed
            if needs_migration:
                self._write_config(config)
                logger.info("Config migration completed successfully")
        except Exception as e:
            logger.warning(f"Config migration failed: {e}")

    def _read_config(self) -> dict[str, Any]:
        """Read configuration from file.

        Returns:
            Dictionary containing the configuration.

        Raises:
            YAMLParseError: If YAML parsing fails.
            ConfigValidationError: If configuration structure is invalid.
            ConfigError: If reading fails for other reasons.
        """
        try:
            with self.config_path.open() as f:
                config = yaml.safe_load(f) or {}

            # Validate config structure
            self._validate_config_structure(config)

            return config
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML configuration: {e}")
            raise YAMLParseError(str(self.config_path), e) from e
        except ConfigValidationError:
            # Re-raise validation errors as-is
            raise
        except OSError as e:
            logger.error(f"Failed to read configuration file: {e}")
            raise ConfigError(f"Failed to read configuration file '{self.config_path}': {e}") from e

    def _write_config(self, config: dict[str, Any]) -> None:
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
                mode="w",
                delete=False,
                dir=self.config_path.parent,
                prefix=".config_",
                suffix=".tmp",
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
        except (OSError, yaml.YAMLError) as e:
            # Clean up temp file if it exists
            if tmp_path:
                try:
                    Path(tmp_path).unlink(missing_ok=True)
                except OSError:
                    logger.warning(f"Failed to clean up temporary file: {tmp_path}")
            logger.error(f"Failed to write configuration file: {e}")
            raise ConfigError(f"Failed to write configuration to '{self.config_path}': {e}") from e

    def _validate_config_structure(self, config: dict[str, Any]) -> None:
        """Validate the configuration structure - basic type checking.

        Args:
            config: Configuration dictionary to validate.

        Raises:
            ConfigValidationError: If configuration structure is invalid.
        """
        if not isinstance(config, dict):
            raise ConfigValidationError("Configuration must be a dictionary")

        # Validate top-level types
        self._validate_top_level_types(config)

        # Validate defaults structure
        self._validate_defaults_types(config)

        # Validate libraries structure
        self._validate_libraries_fields(config)

    def _validate_top_level_types(self, config: dict[str, Any]) -> None:
        """Validate top-level config section types."""
        if "defaults" in config and not isinstance(config["defaults"], dict):
            raise ConfigValidationError("'defaults' must be a dictionary")

        if "preferences" in config and not isinstance(config["preferences"], dict):
            raise ConfigValidationError("'preferences' must be a dictionary")

        if "libraries" in config and not isinstance(config["libraries"], list):
            raise ConfigValidationError("'libraries' must be a list")

    def _validate_defaults_types(self, config: dict[str, Any]) -> None:
        """Validate defaults section has correct types."""
        if "defaults" not in config:
            return

        for module_name, module_defaults in config["defaults"].items():
            if not isinstance(module_defaults, dict):
                raise ConfigValidationError(f"Defaults for module '{module_name}' must be a dictionary")

    def _validate_libraries_fields(self, config: dict[str, Any]) -> None:
        """Validate libraries have required fields."""
        if "libraries" not in config:
            return

        for i, library in enumerate(config["libraries"]):
            if not isinstance(library, dict):
                raise ConfigValidationError(f"Library at index {i} must be a dictionary")

            if "name" not in library:
                raise ConfigValidationError(f"Library at index {i} missing required field 'name'")

            lib_type = library.get("type", "git")
            if lib_type == "git" and ("url" not in library or "directory" not in library):
                raise ConfigValidationError(
                    f"Git library at index {i} missing required fields 'url' and/or 'directory'"
                )
            if lib_type == "static" and "path" not in library:
                raise ConfigValidationError(f"Static library at index {i} missing required field 'path'")

    def get_config_path(self) -> Path:
        """Get the path to the configuration file being used.

        Returns:
            Path to the configuration file (global or local).
        """
        return self.config_path

    def is_using_local_config(self) -> bool:
        """Check if a local configuration file is being used.

        Returns:
            True if using local config, False if using global config.
        """
        return self.is_local

    def get_defaults(self, module_name: str) -> dict[str, Any]:
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

    def set_defaults(self, module_name: str, defaults: dict[str, Any]) -> None:
        """Set default variable values for a module with comprehensive validation.

        Args:
            module_name: Name of the module
            defaults: Dictionary of defaults (flat key-value pairs):
                      {"var_name": "value", "var2_name": "value2"}

        Raises:
            ConfigValidationError: If module name or variable names are invalid.
        """
        # Basic validation
        if not isinstance(module_name, str) or not module_name:
            raise ConfigValidationError("Module name must be a non-empty string")

        if not isinstance(defaults, dict):
            raise ConfigValidationError("Defaults must be a dictionary")

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
        # Basic validation
        if not isinstance(module_name, str) or not module_name:
            raise ConfigValidationError("Module name must be a non-empty string")

        if not isinstance(var_name, str) or not var_name:
            raise ConfigValidationError("Variable name must be a non-empty string")

        defaults = self.get_defaults(module_name)
        defaults[var_name] = value
        self.set_defaults(module_name, defaults)
        logger.info(f"Set default for '{module_name}.{var_name}' = '{value}'")

    def get_default_value(self, module_name: str, var_name: str) -> Any | None:
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

    def get_preference(self, key: str) -> Any | None:
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
        # Basic validation
        if not isinstance(key, str) or not key:
            raise ConfigValidationError("Preference key must be a non-empty string")

        config = self._read_config()

        if "preferences" not in config:
            config["preferences"] = {}

        config["preferences"][key] = value
        self._write_config(config)
        logger.info(f"Set preference '{key}' = '{value}'")

    def get_all_preferences(self) -> dict[str, Any]:
        """Get all user preferences.

        Returns:
            Dictionary of all preferences
        """
        config = self._read_config()
        return config.get("preferences", {})

    def get_libraries(self) -> list[dict[str, Any]]:
        """Get all configured libraries.

        Returns:
            List of library configurations
        """
        config = self._read_config()
        return config.get("libraries", [])

    def get_library_by_name(self, name: str) -> dict[str, Any] | None:
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

    def add_library(self, lib_config: LibraryConfig) -> None:
        """Add a new library to the configuration.

        Args:
            lib_config: Library configuration

        Raises:
            ConfigValidationError: If library with the same name already exists or validation fails
        """
        # Basic validation
        if not isinstance(lib_config.name, str) or not lib_config.name:
            raise ConfigValidationError("Library name must be a non-empty string")

        if lib_config.library_type not in ("git", "static"):
            raise ConfigValidationError(f"Library type must be 'git' or 'static', got '{lib_config.library_type}'")

        if self.get_library_by_name(lib_config.name):
            raise ConfigValidationError(f"Library '{lib_config.name}' already exists")

        # Type-specific validation
        if lib_config.library_type == "git":
            if not lib_config.url or not lib_config.directory:
                raise ConfigValidationError("Git libraries require 'url' and 'directory' parameters")

            library_dict = {
                "name": lib_config.name,
                "type": "git",
                "url": lib_config.url,
                "branch": lib_config.branch,
                "directory": lib_config.directory,
                "enabled": lib_config.enabled,
            }

        else:  # static
            if not lib_config.path:
                raise ConfigValidationError("Static libraries require 'path' parameter")

            # For backward compatibility with older CLI versions,
            # add dummy values for git-specific fields
            library_dict = {
                "name": lib_config.name,
                "type": "static",
                "url": "",  # Empty string for backward compatibility
                "branch": "main",  # Default value for backward compatibility
                "directory": ".",  # Default value for backward compatibility
                "path": lib_config.path,
                "enabled": lib_config.enabled,
            }

        config = self._read_config()

        if "libraries" not in config:
            config["libraries"] = []

        config["libraries"].append(library_dict)

        self._write_config(config)
        logger.info(f"Added {lib_config.library_type} library '{lib_config.name}'")

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
                    library["url"] = kwargs["url"]

                if "branch" in kwargs:
                    library["branch"] = kwargs["branch"]

                if "directory" in kwargs:
                    library["directory"] = kwargs["directory"]

                if "enabled" in kwargs:
                    library["enabled"] = kwargs["enabled"]

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
