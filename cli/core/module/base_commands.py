"""Base commands for module: list, search, show, validate, generate."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from rich.prompt import Confirm
from typer import Exit

from ..display import DisplayManager
from ..exceptions import (
    TemplateRenderError,
    TemplateSyntaxError,
    TemplateValidationError,
)
from .helpers import (
    apply_variable_defaults,
    apply_var_file,
    apply_cli_overrides,
    collect_variable_values,
)

logger = logging.getLogger(__name__)


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
            module_instance.display.display_templates_table(
                filtered_templates,
                module_instance.name,
                f"{module_instance.name.capitalize()} templates",
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
        module_instance.display.display_templates_table(
            filtered_templates,
            module_instance.name,
            f"{module_instance.name.capitalize()} templates matching '{query}'",
        )
    else:
        logger.info(
            f"No templates found matching '{query}' for module '{module_instance.name}'"
        )
        module_instance.display.display_warning(
            f"No templates found matching '{query}'",
            context=f"module '{module_instance.name}'",
        )

    return filtered_templates


def show_template(module_instance, id: str) -> None:
    """Show template details."""
    logger.debug(f"Showing template '{id}' from module '{module_instance.name}'")
    template = module_instance._load_template_by_id(id)

    if not template:
        module_instance.display.display_error(
            f"Template '{id}' not found", context=f"module '{module_instance.name}'"
        )
        return

    # Apply config defaults (same as in generate)
    # This ensures the display shows the actual defaults that will be used
    if template.variables:
        from ..config import ConfigManager

        config = ConfigManager()
        config_defaults = config.get_defaults(module_instance.name)

        if config_defaults:
            logger.debug(f"Loading config defaults for module '{module_instance.name}'")
            # Apply config defaults (this respects the variable types and validation)
            successful = template.variables.apply_defaults(config_defaults, "config")
            if successful:
                logger.debug(f"Applied config defaults for: {', '.join(successful)}")

        # Re-sort sections after applying config (toggle values may have changed)
        template.variables.sort_sections()

        # Reset disabled bool variables to False to prevent confusion
        reset_vars = template.variables.reset_disabled_bool_variables()
        if reset_vars:
            logger.debug(f"Reset {len(reset_vars)} disabled bool variables to False")

    module_instance.display.display_template(template, id)


def check_output_directory(
    output_dir: Path,
    rendered_files: Dict[str, str],
    interactive: bool,
    display: DisplayManager,
) -> Optional[List[Path]]:
    """Check output directory for conflicts and get user confirmation if needed."""
    dir_exists = output_dir.exists()
    dir_not_empty = dir_exists and any(output_dir.iterdir())

    # Check which files already exist
    existing_files = []
    if dir_exists:
        for file_path in rendered_files.keys():
            full_path = output_dir / file_path
            if full_path.exists():
                existing_files.append(full_path)

    # Warn if directory is not empty
    if dir_not_empty:
        if interactive:
            details = []
            if existing_files:
                details.append(f"{len(existing_files)} file(s) will be overwritten.")

            if not display.display_warning_with_confirmation(
                f"Directory '{output_dir}' is not empty.",
                details if details else None,
                default=False,
            ):
                display.display_info("Generation cancelled")
                return None
        else:
            # Non-interactive mode: show warning but continue
            logger.warning(f"Directory '{output_dir}' is not empty")
            if existing_files:
                logger.warning(f"{len(existing_files)} file(s) will be overwritten")

    return existing_files


def get_generation_confirmation(
    output_dir: Path,
    rendered_files: Dict[str, str],
    existing_files: Optional[List[Path]],
    dir_not_empty: bool,
    dry_run: bool,
    interactive: bool,
    display: DisplayManager,
) -> bool:
    """Display file generation confirmation and get user approval."""
    if not interactive:
        return True

    display.display_file_generation_confirmation(
        output_dir, rendered_files, existing_files if existing_files else None
    )

    # Final confirmation (only if we didn't already ask about overwriting)
    if not dir_not_empty and not dry_run:
        if not Confirm.ask("Generate these files?", default=True):
            display.display_info("Generation cancelled")
            return False

    return True


def execute_dry_run(
    id: str,
    output_dir: Path,
    rendered_files: Dict[str, str],
    show_files: bool,
    display: DisplayManager,
) -> None:
    """Execute dry run mode with comprehensive simulation."""
    display.display_info("")
    display.display_info(
        "[bold cyan]Dry Run Mode - Simulating File Generation[/bold cyan]"
    )
    display.display_info("")

    # Simulate directory creation
    display.heading("Directory Operations")

    # Check if output directory exists
    if output_dir.exists():
        display.display_success(f"Output directory exists: [cyan]{output_dir}[/cyan]")
        # Check if we have write permissions
        if os.access(output_dir, os.W_OK):
            display.display_success("Write permission verified")
        else:
            display.display_warning("Write permission may be denied")
    else:
        display.display_info(
            f"  [dim]→[/dim] Would create output directory: [cyan]{output_dir}[/cyan]"
        )
        # Check if parent directory exists and is writable
        parent = output_dir.parent
        if parent.exists() and os.access(parent, os.W_OK):
            display.display_success("Parent directory writable")
        else:
            display.display_warning("Parent directory may not be writable")

    # Collect unique subdirectories that would be created
    subdirs = set()
    for file_path in rendered_files.keys():
        parts = Path(file_path).parts
        for i in range(1, len(parts)):
            subdirs.add(Path(*parts[:i]))

    if subdirs:
        display.display_info(
            f"  [dim]→[/dim] Would create {len(subdirs)} subdirectory(ies)"
        )
        for subdir in sorted(subdirs):
            display.display_info(f"    [dim]📁[/dim] {subdir}/")

    display.display_info("")

    # Display file operations in a table
    display.heading("File Operations")

    total_size = 0
    new_files = 0
    overwrite_files = 0
    file_operations = []

    for file_path, content in sorted(rendered_files.items()):
        full_path = output_dir / file_path
        file_size = len(content.encode("utf-8"))
        total_size += file_size

        # Determine status
        if full_path.exists():
            status = "Overwrite"
            overwrite_files += 1
        else:
            status = "Create"
            new_files += 1

        file_operations.append((file_path, file_size, status))

    display.display_file_operation_table(file_operations)
    display.display_info("")

    # Summary statistics
    if total_size < 1024:
        size_str = f"{total_size}B"
    elif total_size < 1024 * 1024:
        size_str = f"{total_size / 1024:.1f}KB"
    else:
        size_str = f"{total_size / (1024 * 1024):.1f}MB"

    summary_items = {
        "Total files:": str(len(rendered_files)),
        "New files:": str(new_files),
        "Files to overwrite:": str(overwrite_files),
        "Total size:": size_str,
    }
    display.display_summary_table("Summary", summary_items)
    display.display_info("")

    # Show file contents if requested
    if show_files:
        display.display_info("[bold cyan]Generated File Contents:[/bold cyan]")
        display.display_info("")
        for file_path, content in sorted(rendered_files.items()):
            display.display_info(f"[cyan]File:[/cyan] {file_path}")
            display.display_info(f"{'─' * 80}")
            display.display_info(content)
            display.display_info("")  # Add blank line after content
        display.display_info("")

    display.display_success("Dry run complete - no files were written")
    display.display_info(
        f"[dim]Files would have been generated in '{output_dir}'[/dim]"
    )
    logger.info(
        f"Dry run completed for template '{id}' - {len(rendered_files)} files, {total_size} bytes"
    )


def write_generated_files(
    output_dir: Path,
    rendered_files: Dict[str, str],
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
            display.display_success(f"Generated file: {file_path}")

    if not quiet:
        display.display_success(f"Template generated successfully in '{output_dir}'")
    logger.info(f"Template written to directory: {output_dir}")


def generate_template(
    module_instance,
    id: str,
    directory: Optional[str],
    interactive: bool,
    var: Optional[list[str]],
    var_file: Optional[str],
    dry_run: bool,
    show_files: bool,
    quiet: bool,
) -> None:
    """Generate from template."""
    logger.info(
        f"Starting generation for template '{id}' from module '{module_instance.name}'"
    )

    # Create a display manager with quiet mode if needed
    display = DisplayManager(quiet=quiet) if quiet else module_instance.display

    template = module_instance._load_template_by_id(id)

    # Apply defaults and overrides (in precedence order)
    from ..config import ConfigManager

    config = ConfigManager()
    apply_variable_defaults(template, config, module_instance.name)
    apply_var_file(template, var_file, display)
    apply_cli_overrides(template, var)

    # Re-sort sections after all overrides (toggle values may have changed)
    if template.variables:
        template.variables.sort_sections()

        # Reset disabled bool variables to False to prevent confusion
        reset_vars = template.variables.reset_disabled_bool_variables()
        if reset_vars:
            logger.debug(f"Reset {len(reset_vars)} disabled bool variables to False")

    if not quiet:
        module_instance.display.display_template(template, id)
        module_instance.display.display_info("")

    # Collect variable values
    variable_values = collect_variable_values(template, interactive)

    try:
        # Validate and render template
        if template.variables:
            template.variables.validate_all()

        # Check if we're in debug mode (logger level is DEBUG)
        debug_mode = logger.isEnabledFor(logging.DEBUG)

        rendered_files, variable_values = template.render(
            template.variables, debug=debug_mode
        )

        if not rendered_files:
            display.display_error(
                "Template rendering returned no files",
                context="template generation",
            )
            raise Exit(code=1)

        logger.info(f"Successfully rendered template '{id}'")

        # Determine output directory
        if directory:
            output_dir = Path(directory)
            # Check if path looks like an absolute path but is missing the leading slash
            if not output_dir.is_absolute() and str(output_dir).startswith(
                ("Users/", "home/", "usr/", "opt/", "var/", "tmp/")
            ):
                output_dir = Path("/") / output_dir
                logger.debug(
                    f"Normalized relative-looking absolute path to: {output_dir}"
                )
        else:
            output_dir = Path(id)

        # Check for conflicts and get confirmation (skip in quiet mode)
        if not quiet:
            existing_files = check_output_directory(
                output_dir, rendered_files, interactive, display
            )
            if existing_files is None:
                return  # User cancelled

            # Get final confirmation for generation
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
        else:
            # In quiet mode, just check for existing files without prompts
            existing_files = []

        # Execute generation (dry run or actual)
        if dry_run:
            if not quiet:
                execute_dry_run(id, output_dir, rendered_files, show_files, display)
        else:
            write_generated_files(output_dir, rendered_files, quiet, display)

        # Display next steps (not in quiet mode)
        if template.metadata.next_steps and not quiet:
            display.display_next_steps(template.metadata.next_steps, variable_values)

    except TemplateRenderError as e:
        # Display enhanced error information for template rendering errors (always show errors)
        display.display_template_render_error(e, context=f"template '{id}'")
        raise Exit(code=1)
    except Exception as e:
        display.display_error(str(e), context=f"generating template '{id}'")
        raise Exit(code=1)


def validate_templates(
    module_instance,
    template_id: str,
    path: Optional[str],
    verbose: bool,
    semantic: bool,
) -> None:
    """Validate templates for Jinja2 syntax, undefined variables, and semantic correctness."""
    from ..validators import get_validator_registry

    # Validate from path takes precedence
    if path:
        try:
            template_path = Path(path).resolve()
            if not template_path.exists():
                module_instance.display.display_error(f"Path does not exist: {path}")
                raise Exit(code=1)
            if not template_path.is_dir():
                module_instance.display.display_error(
                    f"Path is not a directory: {path}"
                )
                raise Exit(code=1)

            module_instance.display.display_info(
                f"[bold]Validating template from path:[/bold] [cyan]{template_path}[/cyan]"
            )
            from ..template import Template

            template = Template(template_path, library_name="local")
            template_id = template.id
        except Exception as e:
            module_instance.display.display_error(
                f"Failed to load template from path '{path}': {e}"
            )
            raise Exit(code=1)
    elif template_id:
        # Validate a specific template by ID
        try:
            template = module_instance._load_template_by_id(template_id)
            module_instance.display.display_info(
                f"[bold]Validating template:[/bold] [cyan]{template_id}[/cyan]"
            )
        except Exception as e:
            module_instance.display.display_error(
                f"Failed to load template '{template_id}': {e}"
            )
            raise Exit(code=1)
    else:
        # Validate all templates - handled separately below
        template = None

    # Single template validation
    if template:
        try:
            # Trigger validation by accessing used_variables
            _ = template.used_variables
            # Trigger variable definition validation by accessing variables
            _ = template.variables
            module_instance.display.display_success("Jinja2 validation passed")

            # Semantic validation
            if semantic:
                module_instance.display.display_info("")
                module_instance.display.display_info(
                    "[bold cyan]Running semantic validation...[/bold cyan]"
                )
                registry = get_validator_registry()
                has_semantic_errors = False

                # Render template with default values for validation
                debug_mode = logger.isEnabledFor(logging.DEBUG)
                rendered_files, _ = template.render(
                    template.variables, debug=debug_mode
                )

                for file_path, content in rendered_files.items():
                    result = registry.validate_file(content, file_path)

                    if result.errors or result.warnings or (verbose and result.info):
                        module_instance.display.display_info(
                            f"\n[cyan]File:[/cyan] {file_path}"
                        )
                        result.display(f"{file_path}")

                        if result.errors:
                            has_semantic_errors = True

                if not has_semantic_errors:
                    module_instance.display.display_success(
                        "Semantic validation passed"
                    )
                else:
                    module_instance.display.display_error(
                        "Semantic validation found errors"
                    )
                    raise Exit(code=1)

            if verbose:
                module_instance.display.display_info(
                    f"\n[dim]Template path: {template.template_dir}[/dim]"
                )
                module_instance.display.display_info(
                    f"[dim]Found {len(template.used_variables)} variables[/dim]"
                )
                if semantic:
                    module_instance.display.display_info(
                        f"[dim]Generated {len(rendered_files)} files[/dim]"
                    )

        except TemplateRenderError as e:
            # Display enhanced error information for template rendering errors
            module_instance.display.display_template_render_error(
                e, context=f"template '{template_id}'"
            )
            raise Exit(code=1)
        except (TemplateSyntaxError, TemplateValidationError, ValueError) as e:
            module_instance.display.display_error(
                f"Validation failed for '{template_id}':"
            )
            module_instance.display.display_info(f"\n{e}")
            raise Exit(code=1)
        except Exception as e:
            module_instance.display.display_error(
                f"Unexpected error validating '{template_id}': {e}"
            )
            raise Exit(code=1)

        return
    else:
        # Validate all templates
        module_instance.display.display_info(
            f"[bold]Validating all {module_instance.name} templates...[/bold]"
        )

        valid_count = 0
        invalid_count = 0
        errors = []

        # Use centralized helper to load all templates
        all_templates = module_instance._load_all_templates()
        total = len(all_templates)

        for template in all_templates:
            try:
                # Trigger validation
                _ = template.used_variables
                _ = template.variables
                valid_count += 1
                if verbose:
                    module_instance.display.display_success(template.id)
            except ValueError as e:
                invalid_count += 1
                errors.append((template.id, str(e)))
                if verbose:
                    module_instance.display.display_error(template.id)
            except Exception as e:
                invalid_count += 1
                errors.append((template.id, f"Load error: {e}"))
                if verbose:
                    module_instance.display.display_warning(template.id)

        # Summary
        summary_items = {
            "Total templates:": str(total),
            "[green]Valid:[/green]": str(valid_count),
            "[red]Invalid:[/red]": str(invalid_count),
        }
        module_instance.display.display_summary_table(
            "Validation Summary", summary_items
        )

        # Show errors if any
        if errors:
            module_instance.display.display_info("")
            module_instance.display.display_error("Validation Errors:")
            for template_id, error_msg in errors:
                module_instance.display.display_info(
                    f"\n[yellow]Template:[/yellow] [cyan]{template_id}[/cyan]"
                )
                module_instance.display.display_info(f"[dim]{error_msg}[/dim]")
            raise Exit(code=1)
        else:
            module_instance.display.display_success("All templates are valid!")
