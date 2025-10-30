"""Base commands for module: list, search, show, validate, generate."""

from __future__ import annotations

import logging
import os
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
from ..template import Template
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
                name = template.metadata.name or "Unnamed Template"
                tags_list = template.metadata.tags or []
                tags = ",".join(tags_list) if tags_list else "-"
                version = (
                    str(template.metadata.version) if template.metadata.version else "-"
                )
                library = template.metadata.library or "-"
                print(f"{template.id}\t{name}\t{tags}\t{version}\t{library}")
        else:
            # Output rich table format
            def format_template_row(template):
                name = template.metadata.name or "Unnamed Template"
                tags_list = template.metadata.tags or []
                tags = ", ".join(tags_list) if tags_list else "-"
                version = str(template.metadata.version) if template.metadata.version else ""
                schema = template.schema_version if hasattr(template, "schema_version") else "1.0"
                library_name = template.metadata.library or ""
                library_type = template.metadata.library_type or "git"
                # Format library with icon and color
                icon = IconManager.UI_LIBRARY_STATIC if library_type == "static" else IconManager.UI_LIBRARY_GIT
                color = "yellow" if library_type == "static" else "blue"
                library_display = f"[{color}]{icon} {library_name}[/{color}]"
                return (template.id, name, tags, version, schema, library_display)

            module_instance.display.data_table(
                columns=[
                    {"name": "ID", "style": "bold", "no_wrap": True},
                    {"name": "Name"},
                    {"name": "Tags"},
                    {"name": "Version", "no_wrap": True},
                    {"name": "Schema", "no_wrap": True},
                    {"name": "Library", "no_wrap": True},
                ],
                rows=filtered_templates,
                title=f"{module_instance.name.capitalize()} templates",
                row_formatter=format_template_row,
            )
    else:
        logger.info(f"No templates found for module '{module_instance.name}'")

    return filtered_templates


def search_templates(module_instance, query: str) -> list:
    """Search for templates by ID containing the search string."""
    logger.debug(
        f"Searching templates for module '{module_instance.name}' with query='{query}'"
    )

    # Load templates with search filter using centralized helper
    filtered_templates = module_instance._load_all_templates(
        lambda t: query.lower() in t.id.lower()
    )

    if filtered_templates:
        logger.info(
            f"Found {len(filtered_templates)} templates matching '{query}' for module '{module_instance.name}'"
        )
        def format_template_row(template):
            name = template.metadata.name or "Unnamed Template"
            tags_list = template.metadata.tags or []
            tags = ", ".join(tags_list) if tags_list else "-"
            version = str(template.metadata.version) if template.metadata.version else ""
            schema = template.schema_version if hasattr(template, "schema_version") else "1.0"
            library_name = template.metadata.library or ""
            library_type = template.metadata.library_type or "git"
            # Format library with icon and color
            icon = IconManager.UI_LIBRARY_STATIC if library_type == "static" else IconManager.UI_LIBRARY_GIT
            color = "yellow" if library_type == "static" else "blue"
            library_display = f"[{color}]{icon} {library_name}[/{color}]"
            return (template.id, name, tags, version, schema, library_display)

        module_instance.display.data_table(
            columns=[
                {"name": "ID", "style": "bold", "no_wrap": True},
                {"name": "Name"},
                {"name": "Tags"},
                {"name": "Version", "no_wrap": True},
                {"name": "Schema", "no_wrap": True},
                {"name": "Library", "no_wrap": True},
            ],
            rows=filtered_templates,
            title=f"{module_instance.name.capitalize()} templates matching '{query}'",
            row_formatter=format_template_row,
        )
    else:
        logger.info(
            f"No templates found matching '{query}' for module '{module_instance.name}'"
        )
        module_instance.display.warning(
            f"No templates found matching '{query}'",
            context=f"module '{module_instance.name}'",
        )

    return filtered_templates


def show_template(
    module_instance, id: str, var: list[str] | None = None, var_file: str | None = None
) -> None:
    """Show template details with optional variable overrides."""
    logger.debug(f"Showing template '{id}' from module '{module_instance.name}'")
    template = module_instance._load_template_by_id(id)

    if not template:
        module_instance.display.error(
            f"Template '{id}' not found", context=f"module '{module_instance.name}'"
        )
        return

    # Apply defaults and overrides (same precedence as generate command)
    if template.variables:
        config = ConfigManager()
        apply_variable_defaults(template, config, module_instance.name)
        apply_var_file(template, var_file, module_instance.display)
        apply_cli_overrides(template, var)

        # Re-sort sections after applying overrides (toggle values may have changed)
        template.variables.sort_sections()

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
            display.warning(f"Directory '{output_dir}' is not empty.")
            if existing_files:
                display.text(f"  {len(existing_files)} file(s) will be overwritten.")

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


def get_generation_confirmation(
    output_dir: Path,
    rendered_files: dict[str, str],
    existing_files: list[Path] | None,
    dir_not_empty: bool,
    dry_run: bool,
    interactive: bool,
    display: DisplayManager,
) -> bool:
    """Display file generation confirmation and get user approval."""
    if not interactive:
        return True

    # Use templates.render_file_generation_confirmation directly for now
    display.templates.render_file_generation_confirmation(
        output_dir, rendered_files, existing_files if existing_files else None
    )

    # Final confirmation (only if we didn't already ask about overwriting)
    if not dir_not_empty and not dry_run:
        input_mgr = InputManager()
        if not input_mgr.confirm("Generate these files?", default=True):
            display.info("Generation cancelled")
            return False

    return True


def _check_directory_permissions(output_dir: Path, display: DisplayManager) -> None:
    """Check directory existence and write permissions."""
    if output_dir.exists():
        display.success(f"Output directory exists: [cyan]{output_dir}[/cyan]")
        if os.access(output_dir, os.W_OK):
            display.success("Write permission verified")
        else:
            display.warning("Write permission may be denied")
    else:
        display.info(
            f"  [dim]→[/dim] Would create output directory: [cyan]{output_dir}[/cyan]"
        )
        parent = output_dir.parent
        if parent.exists() and os.access(parent, os.W_OK):
            display.success("Parent directory writable")
        else:
            display.warning("Parent directory may not be writable")


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
    elif total_size < BYTES_PER_MB:
        return f"{total_size / BYTES_PER_KB:.1f}KB"
    else:
        return f"{total_size / BYTES_PER_MB:.1f}MB"


def execute_dry_run(
    id: str,
    output_dir: Path,
    rendered_files: dict[str, str],
    show_files: bool,
    display: DisplayManager,
) -> None:
    """Execute dry run mode with comprehensive simulation."""
    display.info("")
    display.info("[bold cyan]Dry Run Mode - Simulating File Generation[/bold cyan]")
    display.info("")

    # Simulate directory creation
    display.heading("Directory Operations")
    _check_directory_permissions(output_dir, display)

    # Collect and display subdirectories
    subdirs = _collect_subdirectories(rendered_files)
    if subdirs:
        display.info(f"  [dim]→[/dim] Would create {len(subdirs)} subdirectory(ies)")
        for subdir in sorted(subdirs):
            display.info(f"    [dim]📁[/dim] {subdir}/")

    display.info("")

    # Display file operations in a table
    display.heading("File Operations")
    file_operations, total_size, new_files, overwrite_files = _analyze_file_operations(
        output_dir, rendered_files
    )
    # Use data_table for file operations
    display.data_table(
        columns=[
            {"name": "File", "no_wrap": False},
            {"name": "Size", "justify": "right", "style": "dim"},
            {"name": "Status", "style": "yellow"},
        ],
        rows=file_operations,
        row_formatter=lambda row: (str(row[0]), display.format_file_size(row[1]), row[2]),
    )
    display.info("")

    # Summary statistics
    size_str = _format_size(total_size)
    summary_rows = [
        ("Total files:", str(len(rendered_files))),
        ("New files:", str(new_files)),
        ("Files to overwrite:", str(overwrite_files)),
        ("Total size:", size_str),
    ]
    display.table(headers=None, rows=summary_rows, title="Summary", show_header=False, borderless=True)
    display.info("")

    # Show file contents if requested
    if show_files:
        display.info("[bold cyan]Generated File Contents:[/bold cyan]")
        display.info("")
        for file_path, content in sorted(rendered_files.items()):
            display.info(f"[cyan]File:[/cyan] {file_path}")
            display.info(f"{'─' * 80}")
            display.info(content)
            display.info("")  # Add blank line after content
        display.info("")

    display.success("Dry run complete - no files were written")
    display.info(f"[dim]Files would have been generated in '{output_dir}'[/dim]")
    logger.info(
        f"Dry run completed for template '{id}' - {len(rendered_files)} files, {total_size} bytes"
    )


def write_generated_files(
    output_dir: Path,
    rendered_files: dict[str, str],
    quiet: bool,
    display: DisplayManager,
) -> None:
    """Write rendered files to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for file_path, content in rendered_files.items():
        full_path = output_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        if not quiet:
            display.success(f"Generated file: {file_path}")

    if not quiet:
        display.success(f"Template generated successfully in '{output_dir}'")
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
        template.variables.sort_sections()
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
    rendered_files, variable_values = template.render(
        template.variables, debug=debug_mode
    )

    if not rendered_files:
        display.error(
            "Template rendering returned no files",
            context="template generation",
        )
        raise Exit(code=1)

    logger.info(f"Successfully rendered template '{id}'")
    return rendered_files, variable_values


def _determine_output_dir(directory: str | None, id: str) -> Path:
    """Determine and normalize output directory path."""
    if directory:
        output_dir = Path(directory)
        if not output_dir.is_absolute() and str(output_dir).startswith(
            ("Users/", "home/", "usr/", "opt/", "var/", "tmp/")
        ):
            output_dir = Path("/") / output_dir
            logger.debug(f"Normalized relative-looking absolute path to: {output_dir}")
    else:
        output_dir = Path(id)
    return output_dir


def generate_template(
    module_instance,
    id: str,
    directory: str | None,
    interactive: bool,
    var: list[str] | None,
    var_file: str | None,
    dry_run: bool,
    show_files: bool,
    quiet: bool,
) -> None:
    """Generate from template."""
    logger.info(
        f"Starting generation for template '{id}' from module '{module_instance.name}'"
    )

    display = DisplayManager(quiet=quiet) if quiet else module_instance.display
    template = _prepare_template(module_instance, id, var_file, var, display)

    if not quiet:
        # Display template header
        module_instance.display.templates.render_template_header(template, id)
        # Display file tree
        module_instance.display.templates.render_file_tree(template)
        # Display variables table
        module_instance.display.variables.render_variables_table(template)
        module_instance.display.info("")

    try:
        rendered_files, variable_values = _render_template(
            template, id, display, interactive
        )
        output_dir = _determine_output_dir(directory, id)

        # Check for conflicts and get confirmation (skip in quiet mode)
        if not quiet:
            existing_files = check_output_directory(
                output_dir, rendered_files, interactive, display
            )
            if existing_files is None:
                return  # User cancelled

            dir_not_empty = output_dir.exists() and any(output_dir.iterdir())
            if not get_generation_confirmation(
                output_dir,
                rendered_files,
                existing_files,
                dir_not_empty,
                dry_run,
                interactive,
                display,
            ):
                return  # User cancelled

        # Execute generation (dry run or actual)
        if dry_run:
            if not quiet:
                execute_dry_run(id, output_dir, rendered_files, show_files, display)
        else:
            write_generated_files(output_dir, rendered_files, quiet, display)

        # Display next steps (not in quiet mode)
        if template.metadata.next_steps and not quiet:
            display.heading("Next Steps")
            try:
                next_steps_template = Jinja2Template(template.metadata.next_steps)
                rendered_next_steps = next_steps_template.render(variable_values)
                display.text(rendered_next_steps)
            except Exception as e:
                logger.warning(f"Failed to render next_steps as template: {e}")
                # Fallback to plain text if rendering fails
                display.text(template.metadata.next_steps)

    except TemplateRenderError as e:
        display.error(str(e), context=f"template '{id}'")
        raise Exit(code=1) from None
    except Exception as e:
        display.error(str(e), context=f"generating template '{id}'")
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
        _validate_single_template(
            module_instance, template, template_id, verbose, semantic
        )
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

        module_instance.display.info(
            f"[bold]Validating template from path:[/bold] [cyan]{template_path}[/cyan]"
        )
        try:
            return Template(template_path, library_name="local")
        except Exception as e:
            module_instance.display.error(
                f"Failed to load template from path '{path}': {e}"
            )
            raise Exit(code=1) from None

    if template_id:
        try:
            template = module_instance._load_template_by_id(template_id)
            module_instance.display.info(
                f"[bold]Validating template:[/bold] [cyan]{template_id}[/cyan]"
            )
            return template
        except Exception as e:
            module_instance.display.error(
                f"Failed to load template '{template_id}': {e}"
            )
            raise Exit(code=1) from None

    return None


def _validate_single_template(
    module_instance, template, template_id: str, verbose: bool, semantic: bool
) -> None:
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
        module_instance.display.error(
            f"Unexpected error validating '{template_id}': {e}"
        )
        raise Exit(code=1) from None


def _run_semantic_validation(module_instance, template, verbose: bool) -> None:
    """Run semantic validation on rendered template files."""
    module_instance.display.info("")
    module_instance.display.info(
        "[bold cyan]Running semantic validation...[/bold cyan]"
    )

    registry = get_validator_registry()
    debug_mode = logger.isEnabledFor(logging.DEBUG)
    rendered_files, _ = template.render(template.variables, debug=debug_mode)

    has_semantic_errors = False
    for file_path, content in rendered_files.items():
        result = registry.validate_file(content, file_path)

        if result.errors or result.warnings or (verbose and result.info):
            module_instance.display.info(f"\n[cyan]File:[/cyan] {file_path}")
            result.display(f"{file_path}")

            if result.errors:
                has_semantic_errors = True

    if has_semantic_errors:
        module_instance.display.error("Semantic validation found errors")
        raise Exit(code=1) from None

    module_instance.display.success("Semantic validation passed")


def _display_validation_details(module_instance, template, semantic: bool) -> None:
    """Display verbose validation details."""
    module_instance.display.info(f"\n[dim]Template path: {template.template_dir}[/dim]")
    module_instance.display.info(
        f"[dim]Found {len(template.used_variables)} variables[/dim]"
    )
    if semantic:
        debug_mode = logger.isEnabledFor(logging.DEBUG)
        rendered_files, _ = template.render(template.variables, debug=debug_mode)
        module_instance.display.info(
            f"[dim]Generated {len(rendered_files)} files[/dim]"
        )


def _validate_all_templates(module_instance, verbose: bool) -> None:
    """Validate all templates in the module."""
    module_instance.display.info(
        f"[bold]Validating all {module_instance.name} templates...[/bold]"
    )

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
    summary_rows = [
        ("Total templates:", str(total)),
        ("[green]Valid:[/green]", str(valid_count)),
        ("[red]Invalid:[/red]", str(invalid_count)),
    ]
    module_instance.display.table(headers=None, rows=summary_rows, title="Validation Summary", show_header=False, borderless=True)

    if errors:
        module_instance.display.info("")
        module_instance.display.error("Validation Errors:")
        for template_id, error_msg in errors:
            module_instance.display.info(
                f"\n[yellow]Template:[/yellow] [cyan]{template_id}[/cyan]"
            )
            module_instance.display.info(f"[dim]{error_msg}[/dim]")
        raise Exit(code=1)

    module_instance.display.success("All templates are valid!")
