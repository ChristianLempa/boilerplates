"""Base module class for template management."""

from __future__ import annotations

import logging
from abc import ABC
from typing import Optional

from typer import Argument, Option, Typer

from ..display import DisplayManager
from ..library import LibraryManager
from .base_commands import (
    list_templates,
    search_templates,
    show_template,
    generate_template,
    validate_templates,
)
from .config_commands import (
    config_get,
    config_set,
    config_remove,
    config_clear,
    config_list,
)

logger = logging.getLogger(__name__)


class Module(ABC):
    """Streamlined base module that auto-detects variables from templates."""

    # Schema version supported by this module (override in subclasses)
    schema_version: str = "1.0"

    def __init__(self) -> None:
        if not all([self.name, self.description]):
            raise ValueError(
                f"Module {self.__class__.__name__} must define name and description"
            )

        logger.info(f"Initializing module '{self.name}'")
        logger.debug(
            f"Module '{self.name}' configuration: description='{self.description}'"
        )
        self.libraries = LibraryManager()
        self.display = DisplayManager()

    def _load_all_templates(self, filter_fn=None) -> list:
        """Load all templates for this module with optional filtering."""
        from ..template import Template

        templates = []
        entries = self.libraries.find(self.name, sort_results=True)

        for entry in entries:
            # Unpack entry - returns (path, library_name, needs_qualification)
            template_dir = entry[0]
            library_name = entry[1]
            needs_qualification = entry[2] if len(entry) > 2 else False

            try:
                # Get library object to determine type
                library = next(
                    (
                        lib
                        for lib in self.libraries.libraries
                        if lib.name == library_name
                    ),
                    None,
                )
                library_type = library.library_type if library else "git"

                template = Template(
                    template_dir, library_name=library_name, library_type=library_type
                )

                # Validate schema version compatibility
                template._validate_schema_version(self.schema_version, self.name)

                # If template ID needs qualification, set qualified ID
                if needs_qualification:
                    template.set_qualified_id()

                # Apply filter if provided
                if filter_fn is None or filter_fn(template):
                    templates.append(template)

            except Exception as exc:
                logger.error(f"Failed to load template from {template_dir}: {exc}")
                continue

        return templates

    def _load_template_by_id(self, id: str):
        """Load a template by its ID, supporting qualified IDs."""
        from ..template import Template

        logger.debug(f"Loading template with ID '{id}' from module '{self.name}'")

        # find_by_id now handles both simple and qualified IDs
        result = self.libraries.find_by_id(self.name, id)

        if not result:
            raise FileNotFoundError(
                f"Template '{id}' not found in module '{self.name}'"
            )

        template_dir, library_name = result

        # Get library type
        library = next(
            (lib for lib in self.libraries.libraries if lib.name == library_name), None
        )
        library_type = library.library_type if library else "git"

        try:
            template = Template(
                template_dir, library_name=library_name, library_type=library_type
            )

            # Validate schema version compatibility
            template._validate_schema_version(self.schema_version, self.name)

            # If the original ID was qualified, preserve it
            if "." in id:
                template.id = id

            return template
        except Exception as exc:
            logger.error(f"Failed to load template '{id}': {exc}")
            raise FileNotFoundError(
                f"Template '{id}' could not be loaded: {exc}"
            ) from exc

    def list(
        self,
        raw: bool = Option(
            False, "--raw", help="Output raw list format instead of rich table"
        ),
    ) -> list:
        """List all templates."""
        return list_templates(self, raw)

    def search(
        self, query: str = Argument(..., help="Search string to filter templates by ID")
    ) -> list:
        """Search for templates by ID containing the search string."""
        return search_templates(self, query)

    def show(self, id: str) -> None:
        """Show template details."""
        return show_template(self, id)

    def generate(
        self,
        id: str = Argument(..., help="Template ID"),
        directory: Optional[str] = Argument(
            None, help="Output directory (defaults to template ID)"
        ),
        interactive: bool = Option(
            True,
            "--interactive/--no-interactive",
            "-i/-n",
            help="Enable interactive prompting for variables",
        ),
        var: Optional[list[str]] = Option(
            None,
            "--var",
            "-v",
            help="Variable override (repeatable). Supports: KEY=VALUE or KEY VALUE",
        ),
        var_file: Optional[str] = Option(
            None,
            "--var-file",
            "-f",
            help="Load variables from YAML file (overrides config defaults, overridden by --var)",
        ),
        dry_run: bool = Option(
            False, "--dry-run", help="Preview template generation without writing files"
        ),
        show_files: bool = Option(
            False,
            "--show-files",
            help="Display generated file contents in plain text (use with --dry-run)",
        ),
        quiet: bool = Option(
            False, "--quiet", "-q", help="Suppress all non-error output"
        ),
    ) -> None:
        """Generate from template.

        Variable precedence chain (lowest to highest):
        1. Module spec (defined in cli/modules/*.py)
        2. Template spec (from template.yaml)
        3. Config defaults (from ~/.config/boilerplates/config.yaml)
        4. Variable file (from --var-file)
        5. CLI overrides (--var flags)
        """
        return generate_template(
            self, id, directory, interactive, var, var_file, dry_run, show_files, quiet
        )

    def validate(
        self,
        template_id: str = Argument(
            None, help="Template ID to validate (if omitted, validates all templates)"
        ),
        path: Optional[str] = Option(
            None,
            "--path",
            "-p",
            help="Validate a template from a specific directory path",
        ),
        verbose: bool = Option(
            False, "--verbose", "-v", help="Show detailed validation information"
        ),
        semantic: bool = Option(
            True,
            "--semantic/--no-semantic",
            help="Enable semantic validation (Docker Compose schema, etc.)",
        ),
    ) -> None:
        """Validate templates for Jinja2 syntax, undefined variables, and semantic correctness."""
        return validate_templates(self, template_id, path, verbose, semantic)

    def config_get(
        self,
        var_name: Optional[str] = Argument(
            None, help="Variable name to get (omit to show all defaults)"
        ),
    ) -> None:
        """Get default value(s) for this module."""
        return config_get(self, var_name)

    def config_set(
        self,
        var_name: str = Argument(..., help="Variable name or var=value format"),
        value: Optional[str] = Argument(
            None, help="Default value (not needed if using var=value format)"
        ),
    ) -> None:
        """Set a default value for a variable."""
        return config_set(self, var_name, value)

    def config_remove(
        self,
        var_name: str = Argument(..., help="Variable name to remove"),
    ) -> None:
        """Remove a specific default variable value."""
        return config_remove(self, var_name)

    def config_clear(
        self,
        var_name: Optional[str] = Argument(
            None, help="Variable name to clear (omit to clear all defaults)"
        ),
        force: bool = Option(False, "--force", "-f", help="Skip confirmation prompt"),
    ) -> None:
        """Clear default value(s) for this module."""
        return config_clear(self, var_name, force)

    def config_list(self) -> None:
        """Display the defaults for this specific module in YAML format."""
        return config_list(self)

    @classmethod
    def register_cli(cls, app: Typer) -> None:
        """Register module commands with the main app."""
        logger.debug(f"Registering CLI commands for module '{cls.name}'")

        module_instance = cls()

        module_app = Typer(help=cls.description)

        module_app.command("list")(module_instance.list)
        module_app.command("search")(module_instance.search)
        module_app.command("show")(module_instance.show)
        module_app.command("validate")(module_instance.validate)

        module_app.command(
            "generate",
            context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
        )(module_instance.generate)

        # Add defaults commands (simplified - only manage default values)
        defaults_app = Typer(help="Manage default values for template variables")
        defaults_app.command("get", help="Get default value(s)")(
            module_instance.config_get
        )
        defaults_app.command("set", help="Set a default value")(
            module_instance.config_set
        )
        defaults_app.command("rm", help="Remove a specific default value")(
            module_instance.config_remove
        )
        defaults_app.command("clear", help="Clear default value(s)")(
            module_instance.config_clear
        )
        defaults_app.command(
            "list", help="Display the config for this module in YAML format"
        )(module_instance.config_list)
        module_app.add_typer(defaults_app, name="defaults")

        app.add_typer(module_app, name=cls.name, help=cls.description)
        logger.info(f"Module '{cls.name}' CLI commands registered")
