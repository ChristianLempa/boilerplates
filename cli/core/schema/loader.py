"""JSON Schema Loading and Validation.

This module provides functionality to load, cache, and validate JSON schemas
for boilerplate modules. Schemas are stored in cli/core/schema/<module>/v*.json files.
"""

import json
from pathlib import Path
from typing import Any

from cli.core.exceptions import SchemaError


class SchemaLoader:
    """Loads and validates JSON schemas for modules."""

    def __init__(self, schema_dir: Path | None = None):
        """Initialize schema loader.

        Args:
            schema_dir: Directory containing schema files. If None, uses cli/core/schema/
        """
        if schema_dir is None:
            # Use path relative to this file (in cli/core/schema/)
            # __file__ is cli/core/schema/loader.py, parent is cli/core/schema/
            self.schema_dir = Path(__file__).parent
        else:
            self.schema_dir = schema_dir

    def load_schema(self, module: str, version: str) -> list[dict[str, Any]]:
        """Load a JSON schema from file.

        Args:
            module: Module name (e.g., 'compose', 'ansible')
            version: Schema version (e.g., '1.0', '1.2')

        Returns:
            Schema as list of section specifications

        Raises:
            SchemaError: If schema file not found or invalid JSON
        """
        schema_file = self.schema_dir / module / f"v{version}.json"

        if not schema_file.exists():
            raise SchemaError(
                f"Schema file not found: {schema_file}",
                details=f"Module: {module}, Version: {version}",
            )

        try:
            with schema_file.open(encoding="utf-8") as f:
                schema = json.load(f)
        except json.JSONDecodeError as e:
            raise SchemaError(
                f"Invalid JSON in schema file: {schema_file}",
                details=f"Error: {e}",
            ) from e
        except Exception as e:
            raise SchemaError(
                f"Failed to read schema file: {schema_file}",
                details=f"Error: {e}",
            ) from e

        # Validate schema structure
        self._validate_schema_structure(schema, module, version)

        return schema

    def _validate_schema_structure(self, schema: Any, module: str, version: str) -> None:
        """Validate that schema has correct structure.

        Args:
            schema: Schema to validate
            module: Module name for error messages
            version: Version for error messages

        Raises:
            SchemaError: If schema structure is invalid
        """
        if not isinstance(schema, list):
            raise SchemaError(
                f"Schema must be a list, got {type(schema).__name__}",
                details=f"Module: {module}, Version: {version}",
            )

        for idx, section in enumerate(schema):
            if not isinstance(section, dict):
                raise SchemaError(
                    f"Section {idx} must be a dict, got {type(section).__name__}",
                    details=f"Module: {module}, Version: {version}",
                )

            # Check required fields
            if "key" not in section:
                raise SchemaError(
                    f"Section {idx} missing required field 'key'",
                    details=f"Module: {module}, Version: {version}",
                )

            if "vars" not in section:
                raise SchemaError(
                    f"Section '{section.get('key')}' missing required field 'vars'",
                    details=f"Module: {module}, Version: {version}",
                )

            if not isinstance(section["vars"], list):
                raise SchemaError(
                    f"Section '{section['key']}' vars must be a list",
                    details=f"Module: {module}, Version: {version}",
                )

            # Validate variables
            for var_idx, var in enumerate(section["vars"]):
                if not isinstance(var, dict):
                    raise SchemaError(
                        f"Variable {var_idx} in section '{section['key']}' must be a dict",
                        details=f"Module: {module}, Version: {version}",
                    )

                if "name" not in var:
                    raise SchemaError(
                        f"Variable {var_idx} in section '{section['key']}' missing 'name'",
                        details=f"Module: {module}, Version: {version}",
                    )

                if "type" not in var:
                    raise SchemaError(
                        f"Variable '{var.get('name')}' in section '{section['key']}' missing 'type'",
                        details=f"Module: {module}, Version: {version}",
                    )

    def list_versions(self, module: str) -> list[str]:
        """List available schema versions for a module.

        Args:
            module: Module name

        Returns:
            List of version strings (e.g., ['1.0', '1.1', '1.2'])
        """
        module_dir = self.schema_dir / module

        if not module_dir.exists():
            return []

        versions = []
        for file in module_dir.glob("v*.json"):
            # Extract version from filename (v1.0.json -> 1.0)
            version = file.stem[1:]  # Remove 'v' prefix
            versions.append(version)

        return sorted(versions)

    def has_schema(self, module: str, version: str) -> bool:
        """Check if a schema exists.

        Args:
            module: Module name
            version: Schema version

        Returns:
            True if schema exists
        """
        schema_file = self.schema_dir / module / f"v{version}.json"
        return schema_file.exists()


# Global schema loader instance
_loader: SchemaLoader | None = None


def get_loader() -> SchemaLoader:
    """Get global schema loader instance.

    Returns:
        SchemaLoader instance
    """
    global _loader  # noqa: PLW0603
    if _loader is None:
        _loader = SchemaLoader()
    return _loader


def load_schema(module: str, version: str) -> list[dict[str, Any]]:
    """Load a schema using the global loader.

    Args:
        module: Module name
        version: Schema version

    Returns:
        Schema as list of section specifications
    """
    return get_loader().load_schema(module, version)


def list_versions(module: str) -> list[str]:
    """List available versions for a module.

    Args:
        module: Module name

    Returns:
        List of version strings
    """
    return get_loader().list_versions(module)


def has_schema(module: str, version: str) -> bool:
    """Check if a schema exists.

    Args:
        module: Module name
        version: Schema version

    Returns:
        True if schema exists
    """
    return get_loader().has_schema(module, version)
