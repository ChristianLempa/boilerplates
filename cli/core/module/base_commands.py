"""Base commands for module: list, search, show, validate, generate."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Template as Jinja2Template
from typer import Exit

from ..config import ConfigManager
from ..display import DisplayManager, IconManager
from ..exceptions import (
    TemplateRenderError,
    TemplateSyntaxError,
    TemplateValidationError,
)
from ..input import InputManager
from ..template import (
    TEMPLATE_STATUS_DRAFT,
    TEMPLATE_STATUS_PUBLISHED,
    Template,
)
from ..validators import get_validator_registry
from .helpers import (
    apply_cli_overrides,
    apply_var_file,
    apply_variable_defaults,
    collect_variable_values,
)

logger = logging.getLogger(__name__)

# File size thresholds for display formatting
BYTES_PER_KB = 1024
BYTES_PER_MB = 1024 * 1024


@dataclass
class GenerationConfig:
    """Configuration for template generation."""

    id: str
    directory: str | None = None
    output: str | None = None
    interactive: bool = True
    var: list[str] | None = None
    var_file: str | None = None
    dry_run: bool = False
    show_files: bool = False
    quiet: bool = False


@dataclass
class ConfirmationContext:
    """Context for file generation confirmation."""

    output_dir: Path
    rendered_files: dict[str, str]
    existing_files: list[Path] | None
    dir_not_empty: bool
    dry_run: bool
    interactive: bool
    display: DisplayManager


def list_templates(module_instance, raw: bool = False) -> list:
    """List all templates."""
    logger.debug(f"Listing templates for module '{module_instance.name}'")

    # Load all templates using centralized helper
    filtered_templates = module_instance._load_all_templates()

    if filtered_templates:
        if raw:
            # Output raw format (tab-separated values for easy filtering with awk/sed/cut)
            # Format: ID\tNAME\tTAGS\tVERSION\tLIBRARY
            for template in filtered_templates:
                tags_list = template.metadata.tags or []
                ",".join(tags_list) if tags_list else "-"
                (str(template.metadata.version) if template.metadata.version else "-")
        else:
            # Output rich table format
            def format_template_row(template):
                name = template.metadata.name or "Unnamed Template"
                tags_list = template.metadata.tags or []
                tags = ", ".join(tags_list) if tags_list else "-"
                version = str(template.metadata.version) if template.metadata.version else ""

                # Get status and format it
                status = template.status
                if status == TEMPLATE_STATUS_PUBLISHED:
                    status_display = "[green]Published[/green]"
                elif status == TEMPLATE_STATUS_DRAFT:
                    status_display = "[dim]Draft[/dim]"
                else:  # TEMPLATE_STATUS_INVALID
                    status_display = "[red]Invalid[/red]"

                library_name = template.metadata.library or ""
                library_type = template.metadata.library_type or "git"
                # Format library with icon and color
                icon = IconManager.UI_LIBRARY_STATIC if library_type == "static" else IconManager.UI_LIBRARY_GIT
                color = "yellow" if library_type == "static" else "blue"
                library_display = f"[{color}]{icon} {library_name}[/{color}]"

                # Apply dimmed style to entire row if draft
                if status == TEMPLATE_STATUS_DRAFT:
                    template_id = f"[dim]{template.id}[/dim]"
                    name = f"[dim]{name}[/dim]"
                    tags = f"[dim]{tags}[/dim]"
                    version = f"[dim]{version}[/dim]"
                    library_display = f"[dim]{icon} {library_name}[/dim]"
                else:
                    template_id = template.id

                return (template_id, name, tags, version, status_display, library_display)

            module_instance.display.data_table(
                columns=[
                    {"name": "ID", "style": "bold", "no_wrap": True},
                    {"name": "Name"},
                    {"name": "Tags"},
                    {"name": "Version", "no_wrap": True},
                    {"name": "Status", "no_wrap": True},
                    {"name": "Library", "no_wrap": True},
                ],
                rows=filtered_templates,
                row_formatter=format_template_row,
            )
    else:
        logger.info(f"No templates found for module '{module_instance.name}'")
        module_instance.display.info(
            f"No templates found for module '{module_instance.name}'",
            context="Use 'bp repo update' to update libraries or check library configuration",
        )

    return filtered_templates


def search_templates(module_instance, query: str) -> list:
    """Search for templates by ID containing the search string."""
    logger.debug(f"Searching templates for module '{module_instance.name}' with query='{query}'")

    # Load templates with search filter using centralized helper
    filtered_templates = module_instance._load_all_templates(lambda t: query.lower() in t.id.lower())

    if filtered_templates:
        logger.info(f"Found {len(filtered_templates)} templates matching '{query}' for module '{module_instance.name}'")

        def format_template_row(template):
            name = template.metadata.name or "Unnamed Template"
            tags_list = template.metadata.tags or []
            tags = ", ".join(tags_list) if tags_list else "-"
            version = str(template.metadata.version) if template.metadata.version else ""

            # Get status and format it
            status = template.status
            if status == TEMPLATE_STATUS_PUBLISHED:
                status_display = "[green]Published[/green]"
            elif status == TEMPLATE_STATUS_DRAFT:
                status_display = "[dim]Draft[/dim]"
            else:  # TEMPLATE_STATUS_INVALID
                status_display = "[red]Invalid[/red]"

            library_name = template.metadata.library or ""
            library_type = template.metadata.library_type or "git"
            # Format library with icon and color
            icon = IconManager.UI_LIBRARY_STATIC if library_type == "static" else IconManager.UI_LIBRARY_GIT
            color = "yellow" if library_type == "static" else "blue"
            library_display = f"[{color}]{icon} {library_name}[/{color}]"

            # Apply dimmed style to entire row if draft
            if status == TEMPLATE_STATUS_DRAFT:
                template_id = f"[dim]{template.id}[/dim]"
                name = f"[dim]{name}[/dim]"
                tags = f"[dim]{tags}[/dim]"
                version = f"[dim]{version}[/dim]"
                library_display = f"[dim]{icon} {library_name}[/dim]"
            else:
                template_id = template.id

            return (template_id, name, tags, version, status_display, library_display)

        module_instance.display.data_table(
            columns=[
                {"name": "ID", "style": "bold", "no_wrap": True},
                {"name": "Name"},
                {"name": "Tags"},
                {"name": "Version", "no_wrap": True},
                {"name": "Status", "no_wrap": True},
                {"name": "Library", "no_wrap": True},
            ],
            rows=filtered_templates,
            row_formatter=format_template_row,
        )
    else:
        logger.info(f"No templates found matching '{query}' for module '{module_instance.name}'")
        module_instance.display.warning(
            f"No templates found matching '{query}'",
            context=f"module '{module_instance.name}'",
        )

    return filtered_templates


def show_template(module_instance, id: str, var: list[str] | None = None, var_file: str | None = None) -> None:
    """Show template details with optional variable overrides."""
    logger.debug(f"Showing template '{id}' from module '{module_instance.name}'")
    template = module_instance._load_template_by_id(id)

    if not template:
        module_instance.display.error(f"Template '{id}' not found", context=f"module '{module_instance.name}'")
        return

    # Apply defaults and overrides (same precedence as generate command)
    if template.variables:
        config = ConfigManager()
        apply_variable_defaults(template, config, module_instance.name)
        apply_var_file(template, var_file, module_instance.display)
        apply_cli_overrides(template, var)

        # Reset disabled bool variables to False to prevent confusion
        reset_vars = template.variables.reset_disabled_bool_variables()
        if reset_vars:
            logger.debug(f"Reset {len(reset_vars)} disabled bool variables to False")

    # Display template header
    module_instance.display.templates.render_template_header(template, id)
    # Display file tree
    module_instance.display.templates.render_file_tree(template)
    # Display variables table
    module_instance.display.variables.render_variables_table(template)


def check_output_directory(
    output_dir: Path,
    rendered_files: dict[str, str],
    interactive: bool,
    display: DisplayManager,
) -> list[Path] | None:
    """Check output directory for conflicts and get user confirmation if needed."""
    dir_exists = output_dir.exists()
    dir_not_empty = dir_exists and any(output_dir.iterdir())

    # Check which files already exist
    existing_files = []
    if dir_exists:
        for file_path in rendered_files:
            full_path = output_dir / file_path
            if full_path.exists():
                existing_files.append(full_path)

    # Warn if directory is not empty
    if dir_not_empty:
        if interactive:
            display.text("")  # Add newline before warning
            # Combine directory warning and file count on same line
            warning_msg = f"Directory '{output_dir}' is not empty."
            if existing_files:
                warning_msg += f" {len(existing_files)} file(s) will be overwritten."
            display.warning(warning_msg)
            display.text("")  # Add newline after warning

            input_mgr = InputManager()
            if not input_mgr.confirm("Continue?", default=False):
                display.info("Generation cancelled")
                return None
        else:
            # Non-interactive mode: show warning but continue
            logger.warning(f"Directory '{output_dir}' is not empty")
            if existing_files:
                logger.warning(f"{len(existing_files)} file(s) will be overwritten")

    return existing_files


def get_generation_confirmation(_ctx: ConfirmationContext) -> bool:
    """Display file generation confirmation and get user approval."""
    # No confirmation needed - either non-interactive, dry-run, or already confirmed during directory check
    return True


def _collect_subdirectories(rendered_files: dict[str, str]) -> set[Path]:
    """Collect unique subdirectories from file paths."""
    subdirs = set()
    for file_path in rendered_files:
        parts = Path(file_path).parts
        for i in range(1, len(parts)):
            subdirs.add(Path(*parts[:i]))
    return subdirs


def _analyze_file_operations(
    output_dir: Path, rendered_files: dict[str, str]
) -> tuple[list[tuple[str, int, str]], int, int, int]:
    """Analyze file operations and return statistics."""
    total_size = 0
    new_files = 0
    overwrite_files = 0
    file_operations = []

    for file_path, content in sorted(rendered_files.items()):
        full_path = output_dir / file_path
        file_size = len(content.encode("utf-8"))
        total_size += file_size

        if full_path.exists():
            status = "Overwrite"
            overwrite_files += 1
        else:
            status = "Create"
            new_files += 1

        file_operations.append((file_path, file_size, status))

    return file_operations, total_size, new_files, overwrite_files


def _format_size(total_size: int) -> str:
    """Format byte size into human-readable string."""
    if total_size < BYTES_PER_KB:
        return f"{total_size}B"
    if total_size < BYTES_PER_MB:
        return f"{total_size / BYTES_PER_KB:.1f}KB"
    return f"{total_size / BYTES_PER_MB:.1f}MB"


def execute_dry_run(
    id: str,
    output_dir: Path,
    rendered_files: dict[str, str],
    show_files: bool,
    display: DisplayManager,
) -> tuple[int, int, str]:
    """Execute dry run mode - preview files without writing.

    Returns:
        Tuple of (total_files, overwrite_files, size_str) for summary display
    """
    _file_operations, total_size, _new_files, overwrite_files = _analyze_file_operations(output_dir, rendered_files)
    size_str = _format_size(total_size)

    # Show file contents if requested
    if show_files:
        display.text("")
        display.heading("File Contents")
        for file_path, content in sorted(rendered_files.items()):
            display.text(f"\n[cyan]{file_path}[/cyan]")
            display.text(f"{'─' * 80}")
            display.text(content)
        display.text("")

    logger.info(f"Dry run completed for template '{id}' - {len(rendered_files)} files, {total_size} bytes")
    return len(rendered_files), overwrite_files, size_str


def write_rendered_files(
    output_dir: Path,
    rendered_files: dict[str, str],
    _quiet: bool,
    _display: DisplayManager,
) -> None:
    """Write rendered files to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for file_path, content in rendered_files.items():
        full_path = output_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with full_path.open("w", encoding="utf-8") as f:
            f.write(content)

    logger.info(f"Template written to directory: {output_dir}")


def _prepare_template(
    module_instance,
    id: str,
    var_file: str | None,
    var: list[str] | None,
    display: DisplayManager,
):
    """Load template and apply all defaults/overrides."""
    template = module_instance._load_template_by_id(id)
    config = ConfigManager()
    apply_variable_defaults(template, config, module_instance.name)
    apply_var_file(template, var_file, display)
    apply_cli_overrides(template, var)

    if template.variables:
        reset_vars = template.variables.reset_disabled_bool_variables()
        if reset_vars:
            logger.debug(f"Reset {len(reset_vars)} disabled bool variables to False")

    return template


def _render_template(template, id: str, display: DisplayManager, interactive: bool):
    """Validate, render template and collect variable values."""
    variable_values = collect_variable_values(template, interactive)

    if template.variables:
        template.variables.validate_all()

    debug_mode = logger.isEnabledFor(logging.DEBUG)
    rendered_files, variable_values = template.render(template.variables, debug=debug_mode)

    if not rendered_files:
        display.error(
            "Template rendering returned no files",
            context="template generation",
        )
        raise Exit(code=1)

    logger.info(f"Successfully rendered template '{id}'")
    return rendered_files, variable_values


def _determine_output_dir(directory: str | None, output: str | None, id: str) -> tuple[Path, bool]:
    """Determine and normalize output directory path.

    Returns:
        Tuple of (output_dir, used_deprecated_arg) where used_deprecated_arg indicates
        if the deprecated positional directory argument was used.
    """
    used_deprecated_arg = False

    # Priority: --output flag > positional directory argument > template ID
    if output:
        output_dir = Path(output)
    elif directory:
        output_dir = Path(directory)
        used_deprecated_arg = True
        logger.debug(f"Using deprecated positional directory argument: {directory}")
    else:
        output_dir = Path(id)

    # Normalize paths that look like absolute paths but are relative
    if not output_dir.is_absolute() and str(output_dir).startswith(("Users/", "home/", "usr/", "opt/", "var/", "tmp/")):
        output_dir = Path("/") / output_dir
        logger.debug(f"Normalized relative-looking absolute path to: {output_dir}")

    return output_dir, used_deprecated_arg


def _display_template_error(display: DisplayManager, template_id: str, error: TemplateRenderError) -> None:
    """Display template rendering error with clean formatting."""
    display.text("")
    display.text("─" * 80, style="dim")
    display.text("")

    # Build details if available
    details = None
    if error.file_path:
        details = error.file_path
        if error.line_number:
            details += f":line {error.line_number}"

    # Display error with details
    display.error(f"Failed to generate boilerplate from template '{template_id}'", details=details)


def _display_generic_error(display: DisplayManager, template_id: str, error: Exception) -> None:
    """Display generic error with clean formatting."""
    display.text("")
    display.text("─" * 80, style="dim")
    display.text("")

    # Truncate long error messages
    max_error_length = 100
    error_msg = str(error)
    if len(error_msg) > max_error_length:
        error_msg = f"{error_msg[:max_error_length]}..."

    # Display error with details
    display.error(f"Failed to generate boilerplate from template '{template_id}'", details=error_msg)


def generate_template(module_instance, config: GenerationConfig) -> None:  # noqa: PLR0912, PLR0915
    """Generate from template."""
    logger.info(f"Starting generation for template '{config.id}' from module '{module_instance.name}'")

    display = DisplayManager(quiet=config.quiet) if config.quiet else module_instance.display
    template = _prepare_template(module_instance, config.id, config.var_file, config.var, display)

    # Determine output directory early to check for deprecated argument usage
    output_dir, used_deprecated_arg = _determine_output_dir(config.directory, config.output, config.id)

    if not config.quiet:
        # Display template header
        module_instance.display.templates.render_template_header(template, config.id)
        # Display file tree
        module_instance.display.templates.render_file_tree(template)
        # Display variables table
        module_instance.display.variables.render_variables_table(template)
        module_instance.display.text("")

        # Show deprecation warning BEFORE any user interaction
        if used_deprecated_arg:
            module_instance.display.warning(
                "Using positional argument for output directory is deprecated and will be removed in v0.2.0",
                details="Use --output/-o flag instead",
            )
            module_instance.display.text("")

    try:
        rendered_files, variable_values = _render_template(template, config.id, display, config.interactive)

        # Check for conflicts and get confirmation (skip in quiet mode)
        if not config.quiet:
            existing_files = check_output_directory(output_dir, rendered_files, config.interactive, display)
            if existing_files is None:
                return  # User cancelled

            dir_not_empty = output_dir.exists() and any(output_dir.iterdir())
            ctx = ConfirmationContext(
                output_dir=output_dir,
                rendered_files=rendered_files,
                existing_files=existing_files,
                dir_not_empty=dir_not_empty,
                dry_run=config.dry_run,
                interactive=config.interactive,
                display=display,
            )
            if not get_generation_confirmation(ctx):
                return  # User cancelled

        # Execute generation (dry run or actual)
        dry_run_stats = None
        if config.dry_run:
            if not config.quiet:
                dry_run_stats = execute_dry_run(config.id, output_dir, rendered_files, config.show_files, display)
        else:
            write_rendered_files(output_dir, rendered_files, config.quiet, display)

        # Display next steps (not in quiet mode)
        if template.metadata.next_steps and not config.quiet:
            display.text("")
            display.heading("Next Steps")
            try:
                next_steps_template = Jinja2Template(template.metadata.next_steps)
                rendered_next_steps = next_steps_template.render(variable_values)
                display.status.markdown(rendered_next_steps)
            except Exception as e:
                logger.warning(f"Failed to render next_steps as template: {e}")
                # Fallback to plain text if rendering fails
                display.status.markdown(template.metadata.next_steps)

        # Display final status message at the end
        if not config.quiet:
            display.text("")
            display.text("─" * 80, style="dim")

            if config.dry_run and dry_run_stats:
                total_files, overwrite_files, size_str = dry_run_stats
                if overwrite_files > 0:
                    display.warning(
                        f"Dry run complete: {total_files} files ({size_str}) would be written to '{output_dir}' "
                        f"({overwrite_files} would be overwritten)"
                    )
                else:
                    display.success(
                        f"Dry run complete: {total_files} files ({size_str}) would be written to '{output_dir}'"
                    )
            else:
                # Actual generation completed
                display.success(f"Boilerplate generated successfully in '{output_dir}'")

    except TemplateRenderError as e:
        _display_template_error(display, config.id, e)
        raise Exit(code=1) from None
    except Exception as e:
        _display_generic_error(display, config.id, e)
        raise Exit(code=1) from None


def validate_templates(
    module_instance,
    template_id: str,
    path: str | None,
    verbose: bool,
    semantic: bool,
) -> None:
    """Validate templates for Jinja2 syntax, undefined variables, and semantic correctness."""
    # Load template based on input
    template = _load_template_for_validation(module_instance, template_id, path)

    if template:
        _validate_single_template(module_instance, template, template_id, verbose, semantic)
    else:
        _validate_all_templates(module_instance, verbose)


def _load_template_for_validation(module_instance, template_id: str, path: str | None):
    """Load a template from path or ID for validation."""
    if path:
        template_path = Path(path).resolve()
        if not template_path.exists():
            module_instance.display.error(f"Path does not exist: {path}")
            raise Exit(code=1) from None
        if not template_path.is_dir():
            module_instance.display.error(f"Path is not a directory: {path}")
            raise Exit(code=1) from None

        module_instance.display.info(f"[bold]Validating template from path:[/bold] [cyan]{template_path}[/cyan]")
        try:
            return Template(template_path, library_name="local")
        except Exception as e:
            module_instance.display.error(f"Failed to load template from path '{path}': {e}")
            raise Exit(code=1) from None

    if template_id:
        try:
            template = module_instance._load_template_by_id(template_id)
            module_instance.display.info(f"Validating template: {template_id}")
            return template
        except Exception as e:
            module_instance.display.error(f"Failed to load template '{template_id}': {e}")
            raise Exit(code=1) from None

    return None


def _validate_single_template(module_instance, template, template_id: str, verbose: bool, semantic: bool) -> None:
    """Validate a single template."""
    try:
        # Jinja2 validation
        _ = template.used_variables
        _ = template.variables
        module_instance.display.success("Jinja2 validation passed")

        # Semantic validation
        if semantic:
            _run_semantic_validation(module_instance, template, verbose)

        # Verbose output
        if verbose:
            _display_validation_details(module_instance, template, semantic)

    except TemplateRenderError as e:
        module_instance.display.error(str(e), context=f"template '{template_id}'")
        raise Exit(code=1) from None
    except (TemplateSyntaxError, TemplateValidationError, ValueError) as e:
        module_instance.display.error(f"Validation failed for '{template_id}':")
        module_instance.display.info(f"\n{e}")
        raise Exit(code=1) from None
    except Exception as e:
        module_instance.display.error(f"Unexpected error validating '{template_id}': {e}")
        raise Exit(code=1) from None


def _run_semantic_validation(module_instance, template, verbose: bool) -> None:
    """Run semantic validation on rendered template files."""
    module_instance.display.info("")
    module_instance.display.info("Running semantic validation...")

    registry = get_validator_registry()
    debug_mode = logger.isEnabledFor(logging.DEBUG)
    rendered_files, _ = template.render(template.variables, debug=debug_mode)

    has_semantic_errors = False
    for file_path, content in rendered_files.items():
        result = registry.validate_file(content, file_path)

        if result.errors or result.warnings or (verbose and result.info):
            module_instance.display.info(f"\nFile: {file_path}")
            result.display(f"{file_path}")

            if result.errors:
                has_semantic_errors = True

    if has_semantic_errors:
        module_instance.display.error("Semantic validation found errors")
        raise Exit(code=1) from None

    module_instance.display.success("Semantic validation passed")


def _display_validation_details(module_instance, template, semantic: bool) -> None:
    """Display verbose validation details."""
    module_instance.display.info(f"\nTemplate path: {template.template_dir}")
    module_instance.display.info(f"Found {len(template.used_variables)} variables")
    if semantic:
        debug_mode = logger.isEnabledFor(logging.DEBUG)
        rendered_files, _ = template.render(template.variables, debug=debug_mode)
        module_instance.display.info(f"Generated {len(rendered_files)} files")


def _validate_all_templates(module_instance, verbose: bool) -> None:
    """Validate all templates in the module."""
    module_instance.display.info(f"Validating all {module_instance.name} templates...")

    valid_count = 0
    invalid_count = 0
    errors = []

    all_templates = module_instance._load_all_templates()
    total = len(all_templates)

    for template in all_templates:
        try:
            _ = template.used_variables
            _ = template.variables
            valid_count += 1
            if verbose:
                module_instance.display.success(template.id)
        except ValueError as e:
            invalid_count += 1
            errors.append((template.id, str(e)))
            if verbose:
                module_instance.display.error(template.id)
        except Exception as e:
            invalid_count += 1
            errors.append((template.id, f"Load error: {e}"))
            if verbose:
                module_instance.display.warning(template.id)

    # Display summary
    module_instance.display.info("")
    module_instance.display.info(f"Total templates: {total}")
    module_instance.display.info(f"Valid: {valid_count}")
    module_instance.display.info(f"Invalid: {invalid_count}")

    if errors:
        module_instance.display.info("")
        for template_id, error_msg in errors:
            module_instance.display.error(f"{template_id}: {error_msg}")
        raise Exit(code=1)

    if total > 0:
        module_instance.display.info("")
        module_instance.display.success("All templates are valid")
