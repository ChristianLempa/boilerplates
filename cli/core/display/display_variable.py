from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rich.table import Table

from .display_icons import IconManager
from .display_settings import DisplaySettings

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..template import Template
    from .display_base import BaseDisplay


class VariableDisplay:
    """Variable-related rendering.

    Provides methods for displaying variables, sections,
    and their values with appropriate formatting based on context.
    """

    def __init__(self, settings: DisplaySettings, base: BaseDisplay):
        """Initialize VariableDisplay.

        Args:
            settings: Display settings for formatting
            base: BaseDisplay instance
        """
        self.settings = settings
        self.base = base

    def render_variable_value(
        self,
        variable,
        _context: str = "default",
        is_dimmed: bool = False,
        var_satisfied: bool = True,
    ) -> str:
        """Render variable value with appropriate formatting based on context.

        Args:
            variable: Variable instance to render
            _context: Display context (unused, kept for API compatibility)
            is_dimmed: Whether the variable should be dimmed
            var_satisfied: Whether the variable's dependencies are satisfied

        Returns:
            Formatted string representation of the variable value
        """
        # Handle disabled bool variables
        if (is_dimmed or not var_satisfied) and variable.type == "bool":
            if hasattr(variable, "_original_disabled") and variable._original_disabled is not False:
                return f"{variable._original_disabled} {IconManager.arrow_right()} False"
            return "False"

        # Handle config overrides with arrow
        if (
            variable.origin == "config"
            and hasattr(variable, "_original_stored")
            and variable.original_value != variable.value
        ):
            settings = self.settings
            orig = self._format_value(
                variable,
                variable.original_value,
                max_length=settings.VALUE_MAX_LENGTH_SHORT,
            )
            curr = variable.get_display_value(
                mask_secret=True,
                max_length=settings.VALUE_MAX_LENGTH_SHORT,
                show_none=False,
            )
            if not curr:
                curr = str(variable.value) if variable.value else settings.TEXT_EMPTY_OVERRIDE
            arrow = IconManager.arrow_right()
            color = settings.COLOR_WARNING
            return f"[dim]{orig}[/dim] [bold {color}]{arrow} {curr}[/bold {color}]"

        # Default formatting
        settings = self.settings
        value = variable.get_display_value(
            mask_secret=True,
            max_length=settings.VALUE_MAX_LENGTH_DEFAULT,
            show_none=True,
        )
        if not variable.value:
            return f"[{settings.COLOR_MUTED}]{value}[/{settings.COLOR_MUTED}]"
        return value

    def _format_value(self, variable, value, max_length: int | None = None) -> str:
        """Helper to format a specific value.

        Args:
            variable: Variable instance
            value: Value to format
            max_length: Maximum length before truncation

        Returns:
            Formatted value string
        """
        settings = self.settings

        if variable.is_secret():
            return settings.SENSITIVE_MASK
        if value is None or value == "":
            return f"[{settings.COLOR_MUTED}]({settings.TEXT_EMPTY_VALUE})[/{settings.COLOR_MUTED}]"

        val_str = str(value)
        return self.base.truncate(val_str, max_length)

    def render_section(self, title: str, description: str | None) -> None:
        """Display a section header.

        Args:
            title: Section title
            description: Optional section description
        """
        settings = self.settings
        if description:
            self.base.text(
                f"\n{title} - {description}",
                style=f"{settings.STYLE_SECTION_TITLE} {settings.STYLE_SECTION_DESC}",
            )
        else:
            self.base.text(f"\n{title}", style=settings.STYLE_SECTION_TITLE)
        self.base.text(
            settings.SECTION_SEPARATOR_CHAR * settings.SECTION_SEPARATOR_LENGTH,
            style=settings.COLOR_MUTED,
        )

    def _render_section_header(self, section, is_dimmed: bool) -> str:
        """Build section header text with appropriate styling.

        Args:
            section: VariableSection instance
            is_dimmed: Whether section is dimmed (disabled)

        Returns:
            Formatted header text with Rich markup
        """
        settings = self.settings
        # Show (disabled) label if section has a toggle and is not enabled
        disabled_text = settings.LABEL_DISABLED if (section.toggle and not section.is_enabled()) else ""

        if is_dimmed:
            style = settings.STYLE_DISABLED
            return f"[bold {style}]{section.title}{disabled_text}[/bold {style}]"
        return f"[bold]{section.title}{disabled_text}[/bold]"

    def _render_variable_options(self, variable) -> str:
        """Render compact variable options/configuration summary."""
        parts: list[str] = []
        config = variable.config

        if variable.type == "enum" and variable.options:
            parts.append(", ".join(variable.options))

        if config:
            parts.extend(self._render_textarea_option(variable, config))
            parts.extend(self._render_integer_options(variable, config))
            parts.extend(self._render_secret_options(variable))

        return self.base.truncate(" | ".join(parts), self.settings.VALUE_MAX_LENGTH_DEFAULT) if parts else ""

    @staticmethod
    def _render_textarea_option(variable, config) -> list[str]:
        if variable.type in {"str", "secret"} and config.textarea:
            return ["textarea"]
        return []

    @staticmethod
    def _render_integer_options(variable, config) -> list[str]:
        if variable.type != "int":
            return []

        parts: list[str] = []
        if config.slider and config.min is not None and config.max is not None:
            slider_part = f"slider {config.min}..{config.max}"
            step = config.step if config.step is not None else 1
            if step != 1:
                slider_part += f" step {step}"
            parts.append(slider_part)
        else:
            bounds = []
            if config.min is not None:
                bounds.append(f"min={config.min}")
            if config.max is not None:
                bounds.append(f"max={config.max}")
            if config.step is not None:
                bounds.append(f"step={config.step}")
            if bounds:
                parts.append(" ".join(bounds))

        if config.unit:
            parts.append(f"unit={config.unit}")

        return parts

    @staticmethod
    def _render_secret_options(variable) -> list[str]:
        if not (variable.is_secret() and variable.autogenerated):
            return []

        if variable.autogenerated_base64:
            bytes_value = (
                variable.autogenerated_config.bytes_or_default()
                if variable.autogenerated_config
                else variable.autogenerated_length
            )
            return [f"autogen base64 bytes={bytes_value}"]

        length = (
            variable.autogenerated_config.length_or_default()
            if variable.autogenerated_config
            else variable.autogenerated_length
        )
        parts = [f"autogen chars len={length}"]
        if variable.autogenerated_config and variable.autogenerated_config.characters:
            parts.append(f"charset={len(variable.autogenerated_config.characters)}")
        return parts

    def _render_variable_row(self, var_name: str, variable, is_dimmed: bool, var_satisfied: bool) -> tuple:
        """Build variable row data for table display.

        Args:
            var_name: Variable name
            variable: Variable instance
            is_dimmed: Whether containing section is dimmed
            var_satisfied: Whether variable dependencies are satisfied

        Returns:
            Tuple of (var_display, type, default_val, options, description, row_style)
        """
        settings = self.settings

        # Build row style
        row_style = settings.STYLE_DISABLED if (is_dimmed or not var_satisfied) else None

        # Build default value
        default_val = self.render_variable_value(variable, is_dimmed=is_dimmed, var_satisfied=var_satisfied)

        # Build variable display name
        secret_icon = f" {IconManager.lock()}" if variable.is_secret() else ""
        # Only show required indicator if variable is enabled (not dimmed and dependencies satisfied)
        required_indicator = settings.LABEL_REQUIRED if variable.required and not is_dimmed and var_satisfied else ""
        var_display = f"{settings.VAR_NAME_INDENT}{var_name}{secret_icon}{required_indicator}"

        return (
            var_display,
            variable.type or "str",
            default_val,
            self._render_variable_options(variable),
            variable.description or "",
            row_style,
        )

    def render_variables_table(self, template: Template) -> None:
        """Display a table of variables for a template.

        All variables and sections are always shown. Disabled sections/variables
        are displayed with dimmed styling.

        Args:
            template: Template instance
        """
        if not (template.variables and template.variables.has_sections()):
            return

        settings = self.settings
        self.base.text("")
        self.base.heading("Template Variables")

        variables_table = Table(show_header=True, header_style=settings.STYLE_TABLE_HEADER)
        variables_table.add_column("Variable", style=settings.STYLE_VAR_COL_NAME, no_wrap=True)
        variables_table.add_column("Type", style=settings.STYLE_VAR_COL_TYPE)
        variables_table.add_column("Default", style=settings.STYLE_VAR_COL_DEFAULT)
        variables_table.add_column("Options", style=settings.STYLE_VAR_COL_DEFAULT)
        variables_table.add_column("Description", style=settings.STYLE_VAR_COL_DESC)

        first_section = True
        for section in template.variables.get_sections().values():
            if not section.variables:
                continue

            if not first_section:
                variables_table.add_row("", "", "", "", "", style=settings.STYLE_DISABLED)
            first_section = False

            # Check if section is enabled AND dependencies are satisfied
            is_enabled = section.is_enabled()
            dependencies_satisfied = template.variables.is_section_satisfied(section.key)
            is_dimmed = not (is_enabled and dependencies_satisfied)

            # Render section header
            header_text = self._render_section_header(section, is_dimmed)
            variables_table.add_row(header_text, "", "", "", "")

            # Render variables
            for var_name, variable in section.variables.items():
                # Check if variable's needs are satisfied
                var_satisfied = template.variables.is_variable_satisfied(var_name)

                # Build and add row
                (
                    var_display,
                    var_type,
                    default_val,
                    options,
                    description,
                    row_style,
                ) = self._render_variable_row(var_name, variable, is_dimmed, var_satisfied)
                variables_table.add_row(var_display, var_type, default_val, options, description, style=row_style)

        self.base._print_table(variables_table)
