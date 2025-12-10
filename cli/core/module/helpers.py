"""Helper methods for module variable application and template generation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import click
import yaml
from typer import Exit

from ..display import DisplayManager
from ..input import PromptHandler

logger = logging.getLogger(__name__)


def parse_var_inputs(var_options: list[str], extra_args: list[str]) -> dict[str, Any]:
    """Parse variable inputs from --var options and extra args with type conversion.

    Supports formats:
      --var KEY=VALUE
      --var KEY VALUE

    Values are automatically converted to appropriate types:
      - 'true', 'yes', '1' → True
      - 'false', 'no', '0' → False
      - Numeric strings → int or float
      - Everything else → string

    Args:
      var_options: List of variable options from CLI
      extra_args: Additional arguments that may contain values

    Returns:
      Dictionary of parsed variables with converted types
    """
    variables = {}

    # Parse --var KEY=VALUE format
    for var_option in var_options:
        if "=" in var_option:
            key, value = var_option.split("=", 1)
            variables[key] = _convert_string_to_type(value)
        # --var KEY VALUE format - value should be in extra_args
        elif extra_args:
            value = extra_args.pop(0)
            variables[var_option] = _convert_string_to_type(value)
        else:
            logger.warning(f"No value provided for variable '{var_option}'")

    return variables


def _convert_string_to_type(value: str) -> Any:
    """Convert string value to appropriate Python type.

    Args:
        value: String value to convert

    Returns:
        Converted value (bool, int, float, or str)
    """
    # Boolean conversion
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False

    # Integer conversion
    try:
        return int(value)
    except ValueError:
        pass

    # Float conversion
    try:
        return float(value)
    except ValueError:
        pass

    # Return as string
    return value


def load_var_file(var_file_path: str) -> dict:
    """Load variables from a YAML file.

    Args:
        var_file_path: Path to the YAML file containing variables

    Returns:
        Dictionary of variable names to values (flat structure)

    Raises:
        FileNotFoundError: If the var file doesn't exist
        ValueError: If the file is not valid YAML or has invalid structure
    """
    var_path = Path(var_file_path).expanduser().resolve()

    if not var_path.exists():
        raise FileNotFoundError(f"Variable file not found: {var_file_path}")

    if not var_path.is_file():
        raise ValueError(f"Variable file path is not a file: {var_file_path}")

    try:
        with var_path.open(encoding="utf-8") as f:
            content = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in variable file: {e}") from e
    except OSError as e:
        raise ValueError(f"Error reading variable file: {e}") from e

    if not isinstance(content, dict):
        raise ValueError(f"Variable file must contain a YAML dictionary, got {type(content).__name__}")

    logger.info(f"Loaded {len(content)} variables from file: {var_path.name}")
    logger.debug(f"Variables from file: {', '.join(content.keys())}")

    return content


def apply_variable_defaults(template, config_manager, module_name: str) -> None:
    """Apply config defaults to template variables.

    Args:
        template: Template instance with variables to configure
        config_manager: ConfigManager instance
        module_name: Name of the module
    """
    if not template.variables:
        return

    config_defaults = config_manager.get_defaults(module_name)

    if config_defaults:
        logger.info(f"Loading config defaults for module '{module_name}'")
        successful = template.variables.apply_defaults(config_defaults, "config")
        if successful:
            logger.debug(f"Applied config defaults for: {', '.join(successful)}")


def apply_var_file(template, var_file_path: str | None, display: DisplayManager) -> None:
    """Apply variables from a YAML file to template.

    Args:
        template: Template instance to apply variables to
        var_file_path: Path to the YAML file containing variables
        display: DisplayManager for error messages

    Raises:
        Exit: If the file cannot be loaded or contains invalid data
    """
    if not var_file_path or not template.variables:
        return

    try:
        var_file_vars = load_var_file(var_file_path)
        if var_file_vars:
            # Get list of valid variable names from template
            valid_vars = set()
            for section in template.variables.get_sections().values():
                valid_vars.update(section.variables.keys())

            # Warn about unknown variables
            unknown_vars = set(var_file_vars.keys()) - valid_vars
            if unknown_vars:
                for var_name in sorted(unknown_vars):
                    logger.warning(f"Variable '{var_name}' from var-file does not exist in template '{template.id}'")

            successful = template.variables.apply_defaults(var_file_vars, "var-file")
            if successful:
                logger.debug(f"Applied var-file overrides for: {', '.join(successful)}")
    except (FileNotFoundError, ValueError) as e:
        display.error(
            f"Failed to load variable file: {e}",
            context="variable file loading",
        )
        raise Exit(code=1) from e


def apply_cli_overrides(template, var: list[str] | None, ctx=None) -> None:
    """Apply CLI variable overrides to template.

    Args:
        template: Template instance to apply overrides to
        var: List of variable override strings from --var flags
        ctx: Context object containing extra args (optional, will get current context if None)
    """
    if not template.variables:
        return

    # Get context if not provided (compatible with all Typer versions)
    if ctx is None:
        try:
            ctx = click.get_current_context()
        except RuntimeError:
            ctx = None

    extra_args = list(ctx.args) if ctx and hasattr(ctx, "args") else []
    cli_overrides = parse_var_inputs(var or [], extra_args)

    if cli_overrides:
        logger.info(f"Received {len(cli_overrides)} variable overrides from CLI")
        successful_overrides = template.variables.apply_defaults(cli_overrides, "cli")
        if successful_overrides:
            logger.debug(f"Applied CLI overrides for: {', '.join(successful_overrides)}")


def collect_variable_values(template, interactive: bool) -> dict[str, Any]:
    """Collect variable values from user prompts and template defaults.

    Args:
        template: Template instance with variables
        interactive: Whether to prompt user for values interactively

    Returns:
        Dictionary of variable names to values
    """
    variable_values = {}

    # Collect values interactively if enabled
    if interactive and template.variables:
        prompt_handler = PromptHandler()
        collected_values = prompt_handler.collect_variables(template.variables)
        if collected_values:
            variable_values.update(collected_values)
            logger.info(f"Collected {len(collected_values)} variable values from user input")

    # Add satisfied variable values (respects dependencies and toggles)
    if template.variables:
        variable_values.update(template.variables.get_satisfied_values())

    return variable_values
