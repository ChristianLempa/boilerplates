"""Semantic validators for template content.

This module provides validators for specific file types and formats,
enabling semantic validation beyond Jinja2 syntax checking.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    pass

import yaml

from .display import DisplayManager

logger = logging.getLogger(__name__)


class ValidationResult:
    """Represents the result of a validation operation."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        logger.error(f"Validation error: {message}")

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
        logger.warning(f"Validation warning: {message}")

    def add_info(self, message: str) -> None:
        """Add an info message."""
        self.info.append(message)
        logger.info(f"Validation info: {message}")

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0

    def display(self, context: str = "Validation") -> None:
        """Display validation results using DisplayManager."""
        display = DisplayManager()

        if self.errors:
            display.error(f"\n✗ {context} Failed:")
            for error in self.errors:
                display.error(f"  • {error}")

        if self.warnings:
            display.warning(f"\n⚠ {context} Warnings:")
            for warning in self.warnings:
                display.warning(f"  • {warning}")

        if self.info:
            display.text(f"\n[blue]i {context} Info:[/blue]")
            for info_msg in self.info:
                display.text(f"  [blue]• {info_msg}[/blue]")

        if self.is_valid and not self.has_warnings:
            display.text(f"\n[green]✓ {context} Passed[/green]")


class ContentValidator(ABC):
    """Abstract base class for content validators."""

    @abstractmethod
    def validate(self, content: str, _file_path: str) -> ValidationResult:
        """Validate content and return results.

        Args:
            content: The file content to validate
            _file_path: Path to the file (unused in base class, kept for API compatibility)

        Returns:
            ValidationResult with errors, warnings, and info
        """
        pass

    @abstractmethod
    def can_validate(self, file_path: str) -> bool:
        """Check if this validator can validate the given file.

        Args:
            file_path: Path to the file

        Returns:
            True if this validator can handle the file
        """
        pass


class DockerComposeValidator(ContentValidator):
    """Validator for Docker Compose files."""

    COMPOSE_FILENAMES: ClassVar[set[str]] = {
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "compose.yaml",
    }

    def can_validate(self, file_path: str) -> bool:
        """Check if file is a Docker Compose file."""
        filename = Path(file_path).name.lower()
        return filename in self.COMPOSE_FILENAMES

    def validate(self, content: str, _file_path: str) -> ValidationResult:
        """Validate Docker Compose file structure."""
        result = ValidationResult()

        try:
            # Parse YAML
            data = yaml.safe_load(content)

            if not isinstance(data, dict):
                result.add_error("Docker Compose file must be a YAML dictionary")
                return result

            # Check for version (optional in Compose v2, but good practice)
            if "version" not in data:
                result.add_info("No 'version' field specified (using Compose v2 format)")

            # Check for services (required)
            if "services" not in data:
                result.add_error("Missing required 'services' section")
                return result

            services = data.get("services", {})
            if not isinstance(services, dict):
                result.add_error("'services' must be a dictionary")
                return result

            if not services:
                result.add_warning("No services defined")

            # Validate each service
            for service_name, service_config in services.items():
                self._validate_service(service_name, service_config, result)

            # Check for networks (optional but recommended)
            if "networks" in data:
                networks = data.get("networks", {})
                if networks and isinstance(networks, dict):
                    result.add_info(f"Defines {len(networks)} network(s)")

            # Check for volumes (optional)
            if "volumes" in data:
                volumes = data.get("volumes", {})
                if volumes and isinstance(volumes, dict):
                    result.add_info(f"Defines {len(volumes)} volume(s)")

        except yaml.YAMLError as e:
            result.add_error(f"YAML parsing error: {e}")
        except Exception as e:
            result.add_error(f"Unexpected validation error: {e}")

        return result

    def _validate_service(self, name: str, config: Any, result: ValidationResult) -> None:
        """Validate a single service configuration."""
        if not isinstance(config, dict):
            result.add_error(f"Service '{name}': configuration must be a dictionary")
            return

        # Check for image or build (at least one required)
        has_image = "image" in config
        has_build = "build" in config

        if not has_image and not has_build:
            result.add_error(f"Service '{name}': must specify 'image' or 'build'")

        # Warn about common misconfigurations
        if "restart" in config:
            restart_value = config["restart"]
            valid_restart_policies = ["no", "always", "on-failure", "unless-stopped"]
            if restart_value not in valid_restart_policies:
                result.add_warning(
                    f"Service '{name}': restart policy '{restart_value}' may be invalid. "
                    f"Valid values: {', '.join(valid_restart_policies)}"
                )

        # Check for environment variables
        if "environment" in config:
            env = config["environment"]
            if isinstance(env, list):
                # Check for duplicate keys in list format
                keys = [e.split("=")[0] for e in env if isinstance(e, str) and "=" in e]
                duplicates = {k for k in keys if keys.count(k) > 1}
                if duplicates:
                    dups = ", ".join(duplicates)
                    result.add_warning(f"Service '{name}': duplicate environment variables: {dups}")

        # Check for ports
        if "ports" in config:
            ports = config["ports"]
            if not isinstance(ports, list):
                result.add_warning(f"Service '{name}': 'ports' should be a list")


class YAMLValidator(ContentValidator):
    """Basic YAML syntax validator."""

    def can_validate(self, file_path: str) -> bool:
        """Check if file is a YAML file."""
        return Path(file_path).suffix.lower() in [".yml", ".yaml"]

    def validate(self, content: str, _file_path: str) -> ValidationResult:
        """Validate YAML syntax."""
        result = ValidationResult()

        try:
            yaml.safe_load(content)
            result.add_info("YAML syntax is valid")
        except yaml.YAMLError as e:
            result.add_error(f"YAML parsing error: {e}")

        return result


class ValidatorRegistry:
    """Registry for content validators."""

    def __init__(self):
        self.validators: list[ContentValidator] = []
        self._register_default_validators()

    def _register_default_validators(self) -> None:
        """Register built-in validators."""
        self.register(DockerComposeValidator())
        self.register(YAMLValidator())

    def register(self, validator: ContentValidator) -> None:
        """Register a validator.

        Args:
            validator: The validator to register
        """
        self.validators.append(validator)
        logger.debug(f"Registered validator: {validator.__class__.__name__}")

    def get_validator(self, file_path: str) -> ContentValidator | None:
        """Get the most appropriate validator for a file.

        Args:
            file_path: Path to the file

        Returns:
            ContentValidator if found, None otherwise
        """
        # Try specific validators first (e.g., DockerComposeValidator before YAMLValidator)
        for validator in self.validators:
            if validator.can_validate(file_path):
                return validator
        return None

    def validate_file(self, content: str, file_path: str) -> ValidationResult:
        """Validate file content using appropriate validator.

        Args:
            content: The file content
            file_path: Path to the file

        Returns:
            ValidationResult with validation results
        """
        validator = self.get_validator(file_path)

        if validator:
            logger.debug(f"Validating {file_path} with {validator.__class__.__name__}")
            return validator.validate(content, file_path)

        # No validator found - return empty result
        result = ValidationResult()
        result.add_info(f"No semantic validator available for {Path(file_path).suffix} files")
        return result


# Global registry instance
_registry = ValidatorRegistry()


def get_validator_registry() -> ValidatorRegistry:
    """Get the global validator registry."""
    return _registry
