"""Base module class for template management."""

from __future__ import annotations

import logging
from abc import ABC
from typing import Annotated

from typer import Argument, Option, Typer

from ..display import DisplayManager
from ..library import LibraryManager
from ..template import Template
from .base_commands import (
    GenerationConfig,
    generate_template,
    list_templates,
    search_templates,
    show_template,
    validate_templates,
)
from .config_commands import (
    config_clear,
    config_get,
    config_list,
    config_remove,
    config_set,
)

logger = logging.getLogger(__name__)

# Expected length of library entry tuple: (path, library_name, needs_qualification)
LIBRARY_ENTRY_MIN_LENGTH = 2


class Module(ABC):
    """Streamlined base module that auto-detects variables from templates.

    Subclasses must define:
    - name: str (class attribute)
    - description: str (class attribute)
    """

    # Class attributes that must be defined by subclasses
    name: str
    description: str

    # Schema version supported by this module (override in subclasses)
    schema_version: str = "1.0"

    def __init__(self) -> None:
        # Validate required class attributes
        if not hasattr(self.__class__, "name") or not hasattr(self.__class__, "description"):
            raise TypeError(f"Module {self.__class__.__name__} must define 'name' and 'description' class attributes")

        logger.info(f"Initializing module '{self.name}'")
        logger.debug(f"Module '{self.name}' configuration: description='{self.description}'")
        self.libraries = LibraryManager()
        self.display = DisplayManager()

    def _load_all_templates(self, filter_fn=None) -> list:
        """Load all templates for this module with optional filtering."""
        templates = []
        entries = self.libraries.find(self.name, sort_results=True)

        for entry in entries:
            # Unpack entry - returns (path, library_name, needs_qualification)
            template_dir = entry[0]
            library_name = entry[1]
            needs_qualification = entry[2] if len(entry) > LIBRARY_ENTRY_MIN_LENGTH else False

            try:
                # Get library object to determine type
                library = next(
                    (lib for lib in self.libraries.libraries if lib.name == library_name),
                    None,
                )
                library_type = library.library_type if library else "git"

                template = Template(template_dir, library_name=library_name, library_type=library_type)

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
        logger.debug(f"Loading template with ID '{id}' from module '{self.name}'")

        # find_by_id now handles both simple and qualified IDs
        result = self.libraries.find_by_id(self.name, id)

        if not result:
            raise FileNotFoundError(f"Template '{id}' not found in module '{self.name}'")

        template_dir, library_name = result

        # Get library type
        library = next((lib for lib in self.libraries.libraries if lib.name == library_name), None)
        library_type = library.library_type if library else "git"

        try:
            template = Template(template_dir, library_name=library_name, library_type=library_type)

            # If the original ID was qualified, preserve it
            if "." in id:
                template.id = id

            return template
        except Exception as exc:
            logger.error(f"Failed to load template '{id}': {exc}")
            raise FileNotFoundError(f"Template '{id}' could not be loaded: {exc}") from exc

    def list(
        self,
        raw: Annotated[bool, Option("--raw", help="Output raw list format instead of rich table")] = False,
    ) -> list:
        """List all templates."""
        return list_templates(self, raw)

    def search(
        self,
        query: Annotated[str, Argument(help="Search string to filter templates by ID")],
    ) -> list:
        """Search for templates by ID containing the search string."""
        return search_templates(self, query)

    def show(
        self,
        id: str,
        var: Annotated[
            list[str] | None,
            Option(
                "--var",
                "-v",
                help="Variable override (repeatable). Supports: KEY=VALUE or KEY VALUE",
            ),
        ] = None,
        var_file: Annotated[
            str | None,
            Option(
                "--var-file",
                "-f",
                help="Load variables from YAML file (overrides config defaults)",
            ),
        ] = None,
    ) -> None:
        """Show template details with optional variable overrides."""
        return show_template(self, id, var, var_file)

    def generate(
        self,
        id: Annotated[str, Argument(help="Template ID")],
        directory: Annotated[
            str | None, Argument(help="[DEPRECATED: use --output] Output directory (defaults to template ID)")
        ] = None,
        *,
        output: Annotated[
            str | None,
            Option(
                "--output",
                "-o",
                help="Output directory (defaults to template ID)",
            ),
        ] = None,
        interactive: Annotated[
            bool,
            Option(
                "--interactive/--no-interactive",
                "-i/-n",
                help="Enable interactive prompting for variables",
            ),
        ] = True,
        var: Annotated[
            list[str] | None,
            Option(
                "--var",
                "-v",
                help="Variable override (repeatable). Supports: KEY=VALUE or KEY VALUE",
            ),
        ] = None,
        var_file: Annotated[
            str | None,
            Option(
                "--var-file",
                "-f",
                help="Load variables from YAML file (overrides config defaults, overridden by --var)",
            ),
        ] = None,
        dry_run: Annotated[
            bool,
            Option("--dry-run", help="Preview template generation without writing files"),
        ] = False,
        show_files: Annotated[
            bool,
            Option(
                "--show-files",
                help="Display generated file contents in plain text (use with --dry-run)",
            ),
        ] = False,
        quiet: Annotated[bool, Option("--quiet", "-q", help="Suppress all non-error output")] = False,
    ) -> None:
        """Generate from template.

        Variable precedence chain (lowest to highest):
        1. Module spec (defined in cli/modules/*.py)
        2. Template spec (from template.yaml)
        3. Config defaults (from ~/.config/boilerplates/config.yaml)
        4. Variable file (from --var-file)
        5. CLI overrides (--var flags)
        """
        config = GenerationConfig(
            id=id,
            directory=directory,
            output=output,
            interactive=interactive,
            var=var,
            var_file=var_file,
            dry_run=dry_run,
            show_files=show_files,
            quiet=quiet,
        )
        return generate_template(self, config)

    def validate(
        self,
        template_id: Annotated[
            str | None,
            Argument(help="Template ID to validate (omit to validate all templates)"),
        ] = None,
        *,
        path: Annotated[
            str | None,
            Option("--path", help="Path to template directory for validation"),
        ] = None,
        verbose: Annotated[bool, Option("--verbose", "-v", help="Show detailed validation information")] = False,
        semantic: Annotated[
            bool,
            Option(
                "--semantic/--no-semantic",
                help="Enable semantic validation (Docker Compose schema, etc.)",
            ),
        ] = True,
    ) -> None:
        """Validate templates for Jinja2 syntax, undefined variables, and semantic correctness.

        Examples:
            # Validate specific template
            cli compose validate netbox

            # Validate all templates
            cli compose validate

            # Validate with verbose output
            cli compose validate netbox --verbose
        """
        return validate_templates(self, template_id, path, verbose, semantic)

    def config_get(
        self,
        var_name: str | None = None,
    ) -> None:
        """Get default value(s) for this module."""
        return config_get(self, var_name)

    def config_set(
        self,
        var_name: str,
        value: str | None = None,
    ) -> None:
        """Set a default value for a variable."""
        return config_set(self, var_name, value)

    def config_remove(
        self,
        var_name: Annotated[str, Argument(help="Variable name to remove")],
    ) -> None:
        """Remove a specific default variable value."""
        return config_remove(self, var_name)

    def config_clear(
        self,
        var_name: str | None = None,
        force: bool = False,
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
        defaults_app.command("get", help="Get default value(s)")(module_instance.config_get)
        defaults_app.command("set", help="Set a default value")(module_instance.config_set)
        defaults_app.command("rm", help="Remove a specific default value")(module_instance.config_remove)
        defaults_app.command("clear", help="Clear default value(s)")(module_instance.config_clear)
        defaults_app.command("list", help="Display the config for this module in YAML format")(
            module_instance.config_list
        )
        module_app.add_typer(defaults_app, name="defaults")

        app.add_typer(
            module_app,
            name=cls.name,
            help=cls.description,
            rich_help_panel="Template Commands",
        )
        logger.info(f"Module '{cls.name}' CLI commands registered")
