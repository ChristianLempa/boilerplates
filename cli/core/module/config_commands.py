"""Config/defaults management commands for module."""

from __future__ import annotations

import logging

from typer import Exit

from cli.core.config import ConfigManager
from cli.core.input import InputManager

logger = logging.getLogger(__name__)


def config_get(module_instance, var_name: str | None = None) -> None:
    """Get default value(s) for this module."""
    config = ConfigManager()

    if var_name:
        # Get specific variable default
        value = config.get_default_value(module_instance.name, var_name)
        if value is not None:
            module_instance.display.info(f"[green]{var_name}[/green] = [yellow]{value}[/yellow]")
        else:
            module_instance.display.warning(
                f"No default set for variable '{var_name}'",
                context=f"module '{module_instance.name}'",
            )
    else:
        # Show all defaults (flat list)
        defaults = config.get_defaults(module_instance.name)
        if defaults:
            module_instance.display.info(f"[bold]Config defaults for module '{module_instance.name}':[/bold]")
            for config_var_name, var_value in defaults.items():
                module_instance.display.info(f"  [green]{config_var_name}[/green] = [yellow]{var_value}[/yellow]")
        else:
            module_instance.display.warning(f"No defaults configured for module '{module_instance.name}'")


def config_set(module_instance, var_name: str, value: str | None = None) -> None:
    """Set a default value for a variable."""
    config = ConfigManager()

    # Parse var_name and value - support both "var value" and "var=value" formats
    if "=" in var_name and value is None:
        # Format: var_name=value
        parts = var_name.split("=", 1)
        actual_var_name = parts[0]
        actual_value = parts[1]
    elif value is not None:
        # Format: var_name value
        actual_var_name = var_name
        actual_value = value
    else:
        module_instance.display.error(f"Missing value for variable '{var_name}'", context="config set")
        module_instance.display.info("[dim]Usage: defaults set VAR_NAME VALUE or defaults set VAR_NAME=VALUE[/dim]")
        raise Exit(code=1)

    # Set the default value
    config.set_default_value(module_instance.name, actual_var_name, actual_value)
    module_instance.display.success(f"Set default: [cyan]{actual_var_name}[/cyan] = [yellow]{actual_value}[/yellow]")
    module_instance.display.info(
        "[dim]This will be used as the default value when generating templates with this module.[/dim]"
    )


def config_remove(module_instance, var_name: str) -> None:
    """Remove a specific default variable value."""
    config = ConfigManager()
    defaults = config.get_defaults(module_instance.name)

    if not defaults:
        module_instance.display.warning(f"No defaults configured for module '{module_instance.name}'")
        return

    if var_name in defaults:
        del defaults[var_name]
        config.set_defaults(module_instance.name, defaults)
        module_instance.display.success(f"Removed default for '{var_name}'")
    else:
        module_instance.display.error(f"No default found for variable '{var_name}'")


def config_clear(module_instance, var_name: str | None = None, force: bool = False) -> None:
    """Clear default value(s) for this module."""
    config = ConfigManager()
    defaults = config.get_defaults(module_instance.name)

    if not defaults:
        module_instance.display.warning(f"No defaults configured for module '{module_instance.name}'")
        return

    if var_name:
        # Clear specific variable
        if var_name in defaults:
            del defaults[var_name]
            config.set_defaults(module_instance.name, defaults)
            module_instance.display.success(f"Cleared default for '{var_name}'")
        else:
            module_instance.display.error(f"No default found for variable '{var_name}'")
    else:
        # Clear all defaults
        if not force:
            detail_lines = [
                f"This will clear ALL defaults for module '{module_instance.name}':",
                "",
            ]
            for clear_var_name, var_value in defaults.items():
                detail_lines.append(f"  [green]{clear_var_name}[/green] = [yellow]{var_value}[/yellow]")

            module_instance.display.warning("Warning: This will clear ALL defaults")
            module_instance.display.info("")
            for line in detail_lines:
                module_instance.display.info(line)
            module_instance.display.info("")
            input_mgr = InputManager()
            if not input_mgr.confirm("Are you sure?", default=False):
                module_instance.display.info("[green]Operation cancelled.[/green]")
                return

        config.clear_defaults(module_instance.name)
        module_instance.display.success(f"Cleared all defaults for module '{module_instance.name}'")


def config_list(module_instance) -> None:
    """Display the defaults for this specific module as a table."""
    config = ConfigManager()

    # Get only the defaults for this module
    defaults = config.get_defaults(module_instance.name)

    if not defaults:
        module_instance.display.warning(f"No defaults configured for module '{module_instance.name}'")
        return

    # Display defaults using DisplayManager
    module_instance.display.heading(f"Defaults for module '{module_instance.name}':")

    # Convert defaults to display format (rows for table)
    rows = [(f"{var_name}:", str(var_value)) for var_name, var_value in defaults.items()]
    module_instance.display.table(headers=None, rows=rows, title="", show_header=False, borderless=True)
