"""Config/defaults management commands for module."""

from __future__ import annotations

import logging
from typing import Optional

from rich.prompt import Confirm
from typer import Exit

logger = logging.getLogger(__name__)


def config_get(module_instance, var_name: Optional[str] = None) -> None:
    """Get default value(s) for this module."""
    from ..config import ConfigManager

    config = ConfigManager()

    if var_name:
        # Get specific variable default
        value = config.get_default_value(module_instance.name, var_name)
        if value is not None:
            module_instance.display.display_info(
                f"[green]{var_name}[/green] = [yellow]{value}[/yellow]"
            )
        else:
            module_instance.display.display_warning(
                f"No default set for variable '{var_name}'",
                context=f"module '{module_instance.name}'",
            )
    else:
        # Show all defaults (flat list)
        defaults = config.get_defaults(module_instance.name)
        if defaults:
            module_instance.display.display_info(
                f"[bold]Config defaults for module '{module_instance.name}':[/bold]"
            )
            for var_name, var_value in defaults.items():
                module_instance.display.display_info(
                    f"  [green]{var_name}[/green] = [yellow]{var_value}[/yellow]"
                )
        else:
            module_instance.display.display_warning(
                f"No defaults configured for module '{module_instance.name}'"
            )


def config_set(module_instance, var_name: str, value: Optional[str] = None) -> None:
    """Set a default value for a variable."""
    from ..config import ConfigManager

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
        module_instance.display.display_error(
            f"Missing value for variable '{var_name}'", context="config set"
        )
        module_instance.display.display_info(
            "[dim]Usage: defaults set VAR_NAME VALUE or defaults set VAR_NAME=VALUE[/dim]"
        )
        raise Exit(code=1)

    # Set the default value
    config.set_default_value(module_instance.name, actual_var_name, actual_value)
    module_instance.display.display_success(
        f"Set default: [cyan]{actual_var_name}[/cyan] = [yellow]{actual_value}[/yellow]"
    )
    module_instance.display.display_info(
        "[dim]This will be used as the default value when generating templates with this module.[/dim]"
    )


def config_remove(module_instance, var_name: str) -> None:
    """Remove a specific default variable value."""
    from ..config import ConfigManager

    config = ConfigManager()
    defaults = config.get_defaults(module_instance.name)

    if not defaults:
        module_instance.display.display_warning(
            f"No defaults configured for module '{module_instance.name}'"
        )
        return

    if var_name in defaults:
        del defaults[var_name]
        config.set_defaults(module_instance.name, defaults)
        module_instance.display.display_success(f"Removed default for '{var_name}'")
    else:
        module_instance.display.display_error(
            f"No default found for variable '{var_name}'"
        )


def config_clear(
    module_instance, var_name: Optional[str] = None, force: bool = False
) -> None:
    """Clear default value(s) for this module."""
    from ..config import ConfigManager

    config = ConfigManager()
    defaults = config.get_defaults(module_instance.name)

    if not defaults:
        module_instance.display.display_warning(
            f"No defaults configured for module '{module_instance.name}'"
        )
        return

    if var_name:
        # Clear specific variable
        if var_name in defaults:
            del defaults[var_name]
            config.set_defaults(module_instance.name, defaults)
            module_instance.display.display_success(f"Cleared default for '{var_name}'")
        else:
            module_instance.display.display_error(
                f"No default found for variable '{var_name}'"
            )
    else:
        # Clear all defaults
        if not force:
            detail_lines = [
                f"This will clear ALL defaults for module '{module_instance.name}':",
                "",
            ]
            for var_name, var_value in defaults.items():
                detail_lines.append(
                    f"  [green]{var_name}[/green] = [yellow]{var_value}[/yellow]"
                )

            module_instance.display.display_warning(
                "Warning: This will clear ALL defaults"
            )
            module_instance.display.display_info("")
            for line in detail_lines:
                module_instance.display.display_info(line)
            module_instance.display.display_info("")
            if not Confirm.ask("[bold red]Are you sure?[/bold red]", default=False):
                module_instance.display.display_info(
                    "[green]Operation cancelled.[/green]"
                )
                return

        config.clear_defaults(module_instance.name)
        module_instance.display.display_success(
            f"Cleared all defaults for module '{module_instance.name}'"
        )


def config_list(module_instance) -> None:
    """Display the defaults for this specific module as a table."""
    from ..config import ConfigManager

    config = ConfigManager()

    # Get only the defaults for this module
    defaults = config.get_defaults(module_instance.name)

    if not defaults:
        module_instance.display.display_warning(
            f"No defaults configured for module '{module_instance.name}'"
        )
        return

    # Display defaults using table primitive
    from rich.table import Table

    settings = module_instance.display.settings

    table = Table(show_header=True, header_style=settings.STYLE_TABLE_HEADER)
    table.add_column("Variable", style=settings.STYLE_VAR_COL_NAME, no_wrap=True)
    table.add_column("Value", style=settings.STYLE_VAR_COL_DEFAULT)

    for var_name, var_value in defaults.items():
        table.add_row(var_name, str(var_value))

    module_instance.display._print_table(table)
