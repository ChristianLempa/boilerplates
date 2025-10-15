from __future__ import annotations

import logging
import sys
from abc import ABC
from pathlib import Path
from typing import Any, Optional, List, Dict, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from typer import Argument, Context, Option, Typer, Exit

from .display import DisplayManager
from .exceptions import (
    TemplateRenderError,
    TemplateSyntaxError,
    TemplateValidationError
)
from .library import LibraryManager
from .prompt import PromptHandler
from .template import Template

logger = logging.getLogger(__name__)
console = Console()
console_err = Console(stderr=True)


def parse_var_inputs(var_options: List[str], extra_args: List[str]) -> Dict[str, Any]:
  """Parse variable inputs from --var options and extra args.
  
  Supports formats:
    --var KEY=VALUE
    --var KEY VALUE
    
  Args:
    var_options: List of variable options from CLI
    extra_args: Additional arguments that may contain values
    
  Returns:
    Dictionary of parsed variables
  """
  variables = {}
  
  # Parse --var KEY=VALUE format
  for var_option in var_options:
    if '=' in var_option:
      key, value = var_option.split('=', 1)
      variables[key] = value
    else:
      # --var KEY VALUE format - value should be in extra_args
      if extra_args:
        variables[var_option] = extra_args.pop(0)
      else:
        logger.warning(f"No value provided for variable '{var_option}'")
  
  return variables

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
    logger.debug(f"Module '{self.name}' configuration: description='{self.description}'")
    self.libraries = LibraryManager()
    self.display = DisplayManager()

  def list(
    self,
    raw: bool = Option(False, "--raw", help="Output raw list format instead of rich table")
  ) -> list[Template]:
    """List all templates."""
    logger.debug(f"Listing templates for module '{self.name}'")
    templates = []

    entries = self.libraries.find(self.name, sort_results=True)
    for entry in entries:
      # Unpack entry - now returns (path, library_name, needs_qualification)
      template_dir = entry[0]
      library_name = entry[1]
      needs_qualification = entry[2] if len(entry) > 2 else False
      
      try:
        # Get library object to determine type
        library = next((lib for lib in self.libraries.libraries if lib.name == library_name), None)
        library_type = library.library_type if library else "git"
        
        template = Template(template_dir, library_name=library_name, library_type=library_type)
        
        # Validate schema version compatibility
        template._validate_schema_version(self.schema_version, self.name)
        
        # If template ID needs qualification, set qualified ID
        if needs_qualification:
          template.set_qualified_id()
        
        templates.append(template)
      except Exception as exc:
        logger.error(f"Failed to load template from {template_dir}: {exc}")
        continue
    
    filtered_templates = templates
    
    if filtered_templates:
      if raw:
        # Output raw format (tab-separated values for easy filtering with awk/sed/cut)
        # Format: ID\tNAME\tTAGS\tVERSION\tLIBRARY
        for template in filtered_templates:
          name = template.metadata.name or "Unnamed Template"
          tags_list = template.metadata.tags or []
          tags = ",".join(tags_list) if tags_list else "-"
          version = str(template.metadata.version) if template.metadata.version else "-"
          library = template.metadata.library or "-"
          print(f"{template.id}\t{name}\t{tags}\t{version}\t{library}")
      else:
        # Output rich table format
        self.display.display_templates_table(
          filtered_templates,
          self.name,
          f"{self.name.capitalize()} templates"
        )
    else:
      logger.info(f"No templates found for module '{self.name}'")

    return filtered_templates

  def search(
    self,
    query: str = Argument(..., help="Search string to filter templates by ID")
  ) -> list[Template]:
    """Search for templates by ID containing the search string."""
    logger.debug(f"Searching templates for module '{self.name}' with query='{query}'")
    templates = []

    entries = self.libraries.find(self.name, sort_results=True)
    for entry in entries:
      # Unpack entry - now returns (path, library_name, needs_qualification)
      template_dir = entry[0]
      library_name = entry[1]
      needs_qualification = entry[2] if len(entry) > 2 else False
      
      try:
        # Get library object to determine type
        library = next((lib for lib in self.libraries.libraries if lib.name == library_name), None)
        library_type = library.library_type if library else "git"
        
        template = Template(template_dir, library_name=library_name, library_type=library_type)
        
        # Validate schema version compatibility
        template._validate_schema_version(self.schema_version, self.name)
        
        # If template ID needs qualification, set qualified ID
        if needs_qualification:
          template.set_qualified_id()
        
        templates.append(template)
      except Exception as exc:
        logger.error(f"Failed to load template from {template_dir}: {exc}")
        continue
    
    # Apply search filtering
    filtered_templates = [t for t in templates if query.lower() in t.id.lower()]
    
    if filtered_templates:
      logger.info(f"Found {len(filtered_templates)} templates matching '{query}' for module '{self.name}'")
      self.display.display_templates_table(
        filtered_templates,
        self.name,
        f"{self.name.capitalize()} templates matching '{query}'"
      )
    else:
      logger.info(f"No templates found matching '{query}' for module '{self.name}'")
      self.display.display_warning(f"No templates found matching '{query}'", context=f"module '{self.name}'")

    return filtered_templates


  def show(
    self,
    id: str,
    all_vars: bool = Option(False, "--all", help="Show all variables/sections, even those with unsatisfied needs"),
  ) -> None:
    """Show template details."""
    logger.debug(f"Showing template '{id}' from module '{self.name}'")
    template = self._load_template_by_id(id)

    if not template:
      self.display.display_error(f"Template '{id}' not found", context=f"module '{self.name}'")
      return
    
    # Apply config defaults (same as in generate)
    # This ensures the display shows the actual defaults that will be used
    if template.variables:
      from .config import ConfigManager
      config = ConfigManager()
      config_defaults = config.get_defaults(self.name)
      
      if config_defaults:
        logger.debug(f"Loading config defaults for module '{self.name}'")
        # Apply config defaults (this respects the variable types and validation)
        successful = template.variables.apply_defaults(config_defaults, "config")
        if successful:
          logger.debug(f"Applied config defaults for: {', '.join(successful)}")
      
      # Re-sort sections after applying config (toggle values may have changed)
      template.variables.sort_sections()
    
    self._display_template_details(template, id, show_all=all_vars)

  def _apply_variable_defaults(self, template: Template) -> None:
    """Apply config defaults and CLI overrides to template variables.
    
    Args:
        template: Template instance with variables to configure
    """
    if not template.variables:
      return
    
    from .config import ConfigManager
    config = ConfigManager()
    config_defaults = config.get_defaults(self.name)
    
    if config_defaults:
      logger.info(f"Loading config defaults for module '{self.name}'")
      successful = template.variables.apply_defaults(config_defaults, "config")
      if successful:
        logger.debug(f"Applied config defaults for: {', '.join(successful)}")

  def _apply_cli_overrides(self, template: Template, var: Optional[List[str]], ctx=None) -> None:
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
      import click
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

  def _collect_variable_values(self, template: Template, interactive: bool) -> Dict[str, Any]:
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
  def _check_output_directory(self, output_dir: Path, rendered_files: Dict[str, str], 
                              interactive: bool) -> Optional[List[Path]]:
    """Check output directory for conflicts and get user confirmation if needed.
    
    Args:
        output_dir: Directory where files will be written
        rendered_files: Dictionary of file paths to rendered content
        interactive: Whether to prompt user for confirmation
        
    Returns:
        List of existing files that will be overwritten, or None to cancel
    """
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
        
        if not self.display.display_warning_with_confirmation(
          f"Directory '{output_dir}' is not empty.",
          details if details else None,
          default=False
        ):
          self.display.display_info("Generation cancelled")
          return None
      else:
        # Non-interactive mode: show warning but continue
        logger.warning(f"Directory '{output_dir}' is not empty")
        if existing_files:
          logger.warning(f"{len(existing_files)} file(s) will be overwritten")
    
    return existing_files

  def _get_generation_confirmation(self, output_dir: Path, rendered_files: Dict[str, str], 
                                    existing_files: Optional[List[Path]], dir_not_empty: bool, 
                                    dry_run: bool, interactive: bool) -> bool:
    """Display file generation confirmation and get user approval.
    
    Args:
        output_dir: Output directory path
        rendered_files: Dictionary of file paths to content
        existing_files: List of existing files that will be overwritten
        dir_not_empty: Whether output directory already contains files
        dry_run: Whether this is a dry run
        interactive: Whether to prompt for confirmation
        
    Returns:
        True if user confirms generation, False to cancel
    """
    if not interactive:
      return True
    
    self.display.display_file_generation_confirmation(
      output_dir, 
      rendered_files, 
      existing_files if existing_files else None
    )
    
    # Final confirmation (only if we didn't already ask about overwriting)
    if not dir_not_empty and not dry_run:
      if not Confirm.ask("Generate these files?", default=True):
        self.display.display_info("Generation cancelled")
        return False
    
    return True

  def _execute_dry_run(self, id: str, output_dir: Path, rendered_files: Dict[str, str], show_files: bool) -> None:
    """Execute dry run mode with comprehensive simulation.
    
    Simulates all filesystem operations that would occur during actual generation,
    including directory creation, file writing, and permission checks.
    
    Args:
        id: Template ID
        output_dir: Directory where files would be written
        rendered_files: Dictionary of file paths to rendered content
        show_files: Whether to display file contents
    """
    import os
    
    console.print()
    console.print("[bold cyan]Dry Run Mode - Simulating File Generation[/bold cyan]")
    console.print()
    
    # Simulate directory creation
    self.display.display_heading("Directory Operations", icon_type="folder")
    
    # Check if output directory exists
    if output_dir.exists():
      self.display.display_success(f"Output directory exists: [cyan]{output_dir}[/cyan]")
      # Check if we have write permissions
      if os.access(output_dir, os.W_OK):
        self.display.display_success("Write permission verified")
      else:
        self.display.display_warning("Write permission may be denied")
    else:
      console.print(f"  [dim]→[/dim] Would create output directory: [cyan]{output_dir}[/cyan]")
      # Check if parent directory exists and is writable
      parent = output_dir.parent
      if parent.exists() and os.access(parent, os.W_OK):
        self.display.display_success("Parent directory writable")
      else:
        self.display.display_warning("Parent directory may not be writable")
    
    # Collect unique subdirectories that would be created
    subdirs = set()
    for file_path in rendered_files.keys():
      parts = Path(file_path).parts
      for i in range(1, len(parts)):
        subdirs.add(Path(*parts[:i]))
    
    if subdirs:
      console.print(f"  [dim]→[/dim] Would create {len(subdirs)} subdirectory(ies)")
      for subdir in sorted(subdirs):
        console.print(f"    [dim]📁[/dim] {subdir}/")
    
    console.print()
    
    # Display file operations in a table
    self.display.display_heading("File Operations", icon_type="file")
    
    total_size = 0
    new_files = 0
    overwrite_files = 0
    file_operations = []
    
    for file_path, content in sorted(rendered_files.items()):
      full_path = output_dir / file_path
      file_size = len(content.encode('utf-8'))
      total_size += file_size
      
      # Determine status
      if full_path.exists():
        status = "Overwrite"
        overwrite_files += 1
      else:
        status = "Create"
        new_files += 1
      
      file_operations.append((file_path, file_size, status))
    
    self.display.display_file_operation_table(file_operations)
    console.print()
    
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
      "Total size:": size_str
    }
    self.display.display_summary_table("Summary", summary_items)
    console.print()
    
    # Show file contents if requested
    if show_files:
      console.print("[bold cyan]Generated File Contents:[/bold cyan]")
      console.print()
      for file_path, content in sorted(rendered_files.items()):
        console.print(f"[cyan]File:[/cyan] {file_path}")
        print(f"{'─'*80}")
        print(content)
        print()  # Add blank line after content
      console.print()
    
    self.display.display_success("Dry run complete - no files were written")
    console.print(f"[dim]Files would have been generated in '{output_dir}'[/dim]")
    logger.info(f"Dry run completed for template '{id}' - {len(rendered_files)} files, {total_size} bytes")

  def _write_generated_files(self, output_dir: Path, rendered_files: Dict[str, str], quiet: bool = False) -> None:
    """Write rendered files to the output directory.
    
    Args:
        output_dir: Directory to write files to
        rendered_files: Dictionary of file paths to rendered content
        quiet: Suppress output messages
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for file_path, content in rendered_files.items():
      full_path = output_dir / file_path
      full_path.parent.mkdir(parents=True, exist_ok=True)
      with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
      if not quiet:
        console.print(f"[green]Generated file: {file_path}[/green]")  # Keep simple per-file output
    
    if not quiet:
      self.display.display_success(f"Template generated successfully in '{output_dir}'")
    logger.info(f"Template written to directory: {output_dir}")

  def generate(
    self,
    id: str = Argument(..., help="Template ID"),
    directory: Optional[str] = Argument(None, help="Output directory (defaults to template ID)"),
    interactive: bool = Option(True, "--interactive/--no-interactive", "-i/-n", help="Enable interactive prompting for variables"),
    var: Optional[list[str]] = Option(None, "--var", "-v", help="Variable override (repeatable). Supports: KEY=VALUE or KEY VALUE"),
    dry_run: bool = Option(False, "--dry-run", help="Preview template generation without writing files"),
    show_files: bool = Option(False, "--show-files", help="Display generated file contents in plain text (use with --dry-run)"),
    quiet: bool = Option(False, "--quiet", "-q", help="Suppress all non-error output"),
    all_vars: bool = Option(False, "--all", help="Show all variables/sections, even those with unsatisfied needs"),
  ) -> None:
    """Generate from template.
    
    Variable precedence chain (lowest to highest):
    1. Module spec (defined in cli/modules/*.py)
    2. Template spec (from template.yaml)
    3. Config defaults (from ~/.config/boilerplates/config.yaml)
    4. CLI overrides (--var flags)
    
    Examples:
        # Generate to directory named after template
        cli compose generate traefik
        
        # Generate to custom directory
        cli compose generate traefik my-proxy
        
        # Generate with variables
        cli compose generate traefik --var traefik_enabled=false
        
        # Preview without writing files (dry run)
        cli compose generate traefik --dry-run
        
        # Preview and show generated file contents
        cli compose generate traefik --dry-run --show-files
    """
    logger.info(f"Starting generation for template '{id}' from module '{self.name}'")
    
    # Create a display manager with quiet mode if needed
    display = DisplayManager(quiet=quiet) if quiet else self.display
    
    template = self._load_template_by_id(id)

    # Apply defaults and overrides
    self._apply_variable_defaults(template)
    self._apply_cli_overrides(template, var)
    
    # Re-sort sections after all overrides (toggle values may have changed)
    if template.variables:
      template.variables.sort_sections()

    if not quiet:
      self._display_template_details(template, id, show_all=all_vars)
      console.print()

    # Collect variable values
    variable_values = self._collect_variable_values(template, interactive)

    try:
      # Validate and render template
      if template.variables:
        template.variables.validate_all()
      
      # Check if we're in debug mode (logger level is DEBUG)
      debug_mode = logger.isEnabledFor(logging.DEBUG)
      
      rendered_files, variable_values = template.render(template.variables, debug=debug_mode)
      
      if not rendered_files:
        display.display_error("Template rendering returned no files", context="template generation")
        raise Exit(code=1)
      
      logger.info(f"Successfully rendered template '{id}'")
      
      # Determine output directory
      if directory:
        output_dir = Path(directory)
        # Check if path looks like an absolute path but is missing the leading slash
        # This handles cases like "Users/username/path" which should be "/Users/username/path"
        if not output_dir.is_absolute() and str(output_dir).startswith(("Users/", "home/", "usr/", "opt/", "var/", "tmp/")):
          output_dir = Path("/") / output_dir
          logger.debug(f"Normalized relative-looking absolute path to: {output_dir}")
      else:
        output_dir = Path(id)
      
      # Check for conflicts and get confirmation (skip in quiet mode)
      if not quiet:
        existing_files = self._check_output_directory(output_dir, rendered_files, interactive)
        if existing_files is None:
          return  # User cancelled
        
        # Get final confirmation for generation
        dir_not_empty = output_dir.exists() and any(output_dir.iterdir())
        if not self._get_generation_confirmation(output_dir, rendered_files, existing_files, 
                                                 dir_not_empty, dry_run, interactive):
          return  # User cancelled
      else:
        # In quiet mode, just check for existing files without prompts
        existing_files = []
      
      # Execute generation (dry run or actual)
      if dry_run:
        if not quiet:
          self._execute_dry_run(id, output_dir, rendered_files, show_files)
      else:
        self._write_generated_files(output_dir, rendered_files, quiet=quiet)
      
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

  def config_get(
    self,
    var_name: Optional[str] = Argument(None, help="Variable name to get (omit to show all defaults)"),
  ) -> None:
    """Get default value(s) for this module.
    
    Examples:
        # Get all defaults for module
        cli compose defaults get
        
        # Get specific variable default
        cli compose defaults get service_name
    """
    from .config import ConfigManager
    config = ConfigManager()
    
    if var_name:
      # Get specific variable default
      value = config.get_default_value(self.name, var_name)
      if value is not None:
        console.print(f"[green]{var_name}[/green] = [yellow]{value}[/yellow]")
      else:
        self.display.display_warning(f"No default set for variable '{var_name}'", context=f"module '{self.name}'")
    else:
      # Show all defaults (flat list)
      defaults = config.get_defaults(self.name)
      if defaults:
        console.print(f"[bold]Config defaults for module '{self.name}':[/bold]\n")
        for var_name, var_value in defaults.items():
          console.print(f"  [green]{var_name}[/green] = [yellow]{var_value}[/yellow]")
      else:
        console.print(f"[yellow]No defaults configured for module '{self.name}'[/yellow]")

  def config_set(
    self,
    var_name: str = Argument(..., help="Variable name or var=value format"),
    value: Optional[str] = Argument(None, help="Default value (not needed if using var=value format)"),
  ) -> None:
    """Set a default value for a variable.
    
    This only sets the DEFAULT VALUE, not the variable spec.
    The variable must be defined in the module or template spec.
    
    Supports both formats:
      - var_name value
      - var_name=value
    
    Examples:
        # Set default value (format 1)
        cli compose defaults set service_name my-awesome-app
        
        # Set default value (format 2)
        cli compose defaults set service_name=my-awesome-app
        
        # Set author for all compose templates
        cli compose defaults set author "Christian Lempa"
    """
    from .config import ConfigManager
    config = ConfigManager()
    
    # Parse var_name and value - support both "var value" and "var=value" formats
    if '=' in var_name and value is None:
      # Format: var_name=value
      parts = var_name.split('=', 1)
      actual_var_name = parts[0]
      actual_value = parts[1]
    elif value is not None:
      # Format: var_name value
      actual_var_name = var_name
      actual_value = value
    else:
      self.display.display_error(f"Missing value for variable '{var_name}'", context="config set")
      console.print(f"[dim]Usage: defaults set VAR_NAME VALUE or defaults set VAR_NAME=VALUE[/dim]")
      raise Exit(code=1)
    
    # Set the default value
    config.set_default_value(self.name, actual_var_name, actual_value)
    self.display.display_success(f"Set default: [cyan]{actual_var_name}[/cyan] = [yellow]{actual_value}[/yellow]")
    console.print(f"\n[dim]This will be used as the default value when generating templates with this module.[/dim]")

  def config_remove(
    self,
    var_name: str = Argument(..., help="Variable name to remove"),
  ) -> None:
    """Remove a specific default variable value.
    
    Examples:
        # Remove a default value
        cli compose defaults rm service_name
    """
    from .config import ConfigManager
    config = ConfigManager()
    defaults = config.get_defaults(self.name)
    
    if not defaults:
      console.print(f"[yellow]No defaults configured for module '{self.name}'[/yellow]")
      return
    
    if var_name in defaults:
      del defaults[var_name]
      config.set_defaults(self.name, defaults)
      self.display.display_success(f"Removed default for '{var_name}'")
    else:
      self.display.display_error(f"No default found for variable '{var_name}'")

  def config_clear(
    self,
    var_name: Optional[str] = Argument(None, help="Variable name to clear (omit to clear all defaults)"),
    force: bool = Option(False, "--force", "-f", help="Skip confirmation prompt"),
  ) -> None:
    """Clear default value(s) for this module.
    
    Examples:
        # Clear specific variable default
        cli compose defaults clear service_name
        
        # Clear all defaults for module
        cli compose defaults clear --force
    """
    from .config import ConfigManager
    config = ConfigManager()
    defaults = config.get_defaults(self.name)
    
    if not defaults:
      console.print(f"[yellow]No defaults configured for module '{self.name}'[/yellow]")
      return
    
    if var_name:
      # Clear specific variable
      if var_name in defaults:
        del defaults[var_name]
        config.set_defaults(self.name, defaults)
        self.display.display_success(f"Cleared default for '{var_name}'")
      else:
        self.display.display_error(f"No default found for variable '{var_name}'")
    else:
      # Clear all defaults
      if not force:
        detail_lines = [f"This will clear ALL defaults for module '{self.name}':", ""]
        for var_name, var_value in defaults.items():
          detail_lines.append(f"  [green]{var_name}[/green] = [yellow]{var_value}[/yellow]")
        
        self.display.display_warning("Warning: This will clear ALL defaults")
        console.print()
        for line in detail_lines:
          console.print(line)
        console.print()
        if not Confirm.ask(f"[bold red]Are you sure?[/bold red]", default=False):
          console.print("[green]Operation cancelled.[/green]")
          return
      
      config.clear_defaults(self.name)
      self.display.display_success(f"Cleared all defaults for module '{self.name}'")

  def config_list(self) -> None:
    """Display the defaults for this specific module in YAML format.
    
    Examples:
        # Show the defaults for the current module
        cli compose defaults list
    """
    from .config import ConfigManager
    import yaml
    
    config = ConfigManager()
    
    # Get only the defaults for this module
    defaults = config.get_defaults(self.name)
    
    if not defaults:
      console.print(f"[yellow]No configuration found for module '{self.name}'[/yellow]")
      console.print(f"\n[dim]Config file location: {config.get_config_path()}[/dim]")
      return
    
    # Create a minimal config structure with only this module's defaults
    module_config = {
      "defaults": {
        self.name: defaults
      }
    }
    
    # Convert config to YAML string
    yaml_output = yaml.dump(module_config, default_flow_style=False, sort_keys=False)
    
    console.print(f"[bold]Configuration for module:[/bold] [cyan]{self.name}[/cyan]")
    console.print(f"[dim]Config file: {config.get_config_path()}[/dim]\n")
    console.print(Panel(yaml_output, title=f"{self.name.capitalize()} Config", border_style="blue"))

  def validate(
    self,
    template_id: str = Argument(None, help="Template ID to validate (if omitted, validates all templates)"),
    path: Optional[str] = Option(None, "--path", "-p", help="Validate a template from a specific directory path"),
    verbose: bool = Option(False, "--verbose", "-v", help="Show detailed validation information"),
    semantic: bool = Option(True, "--semantic/--no-semantic", help="Enable semantic validation (Docker Compose schema, etc.)")
  ) -> None:
    """Validate templates for Jinja2 syntax, undefined variables, and semantic correctness.
    
    Validation includes:
    - Jinja2 syntax checking
    - Variable definition checking
    - Semantic validation (when --semantic is enabled):
      - Docker Compose file structure
      - YAML syntax
      - Configuration best practices
    
    Examples:
        # Validate all templates in this module
        cli compose validate
        
        # Validate a specific template
        cli compose validate gitlab
        
        # Validate a template from a specific path
        cli compose validate --path /path/to/template
        
        # Validate with verbose output
        cli compose validate --verbose
        
        # Skip semantic validation (only Jinja2)
        cli compose validate --no-semantic
    """
    from rich.table import Table
    from .validators import get_validator_registry
    
    # Validate from path takes precedence
    if path:
      try:
        template_path = Path(path).resolve()
        if not template_path.exists():
          self.display.display_error(f"Path does not exist: {path}")
          raise Exit(code=1)
        if not template_path.is_dir():
          self.display.display_error(f"Path is not a directory: {path}")
          raise Exit(code=1)
        
        console.print(f"[bold]Validating template from path:[/bold] [cyan]{template_path}[/cyan]\n")
        template = Template(template_path, library_name="local")
        template_id = template.id
      except Exception as e:
        self.display.display_error(f"Failed to load template from path '{path}': {e}")
        raise Exit(code=1)
    elif template_id:
      # Validate a specific template by ID
      try:
        template = self._load_template_by_id(template_id)
        console.print(f"[bold]Validating template:[/bold] [cyan]{template_id}[/cyan]\n")
      except Exception as e:
        self.display.display_error(f"Failed to load template '{template_id}': {e}")
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
        self.display.display_success("Jinja2 validation passed")
        
        # Semantic validation
        if semantic:
          console.print(f"\n[bold cyan]Running semantic validation...[/bold cyan]")
          registry = get_validator_registry()
          has_semantic_errors = False
          
          # Render template with default values for validation
          debug_mode = logger.isEnabledFor(logging.DEBUG)
          rendered_files, _ = template.render(template.variables, debug=debug_mode)
          
          for file_path, content in rendered_files.items():
            result = registry.validate_file(content, file_path)
            
            if result.errors or result.warnings or (verbose and result.info):
              console.print(f"\n[cyan]File:[/cyan] {file_path}")
              result.display(f"{file_path}")
              
              if result.errors:
                has_semantic_errors = True
          
          if not has_semantic_errors:
            self.display.display_success("Semantic validation passed")
          else:
            self.display.display_error("Semantic validation found errors")
            raise Exit(code=1)
        
        if verbose:
          console.print(f"\n[dim]Template path: {template.template_dir}[/dim]")
          console.print(f"[dim]Found {len(template.used_variables)} variables[/dim]")
          if semantic:
            console.print(f"[dim]Generated {len(rendered_files)} files[/dim]")
      
      except TemplateRenderError as e:
        # Display enhanced error information for template rendering errors
        self.display.display_template_render_error(e, context=f"template '{template_id}'")
        raise Exit(code=1)
      except (TemplateSyntaxError, TemplateValidationError, ValueError) as e:
        self.display.display_error(f"Validation failed for '{template_id}':")
        console.print(f"\n{e}")
        raise Exit(code=1)
      except Exception as e:
        self.display.display_error(f"Unexpected error validating '{template_id}': {e}")
        raise Exit(code=1)
      
      return
    else:
      # Validate all templates
      console.print(f"[bold]Validating all {self.name} templates...[/bold]\n")
      
      entries = self.libraries.find(self.name, sort_results=True)
      total = len(entries)
      valid_count = 0
      invalid_count = 0
      errors = []
      
      for template_dir, library_name in entries:
        template_id = template_dir.name
        try:
          template = Template(template_dir, library_name=library_name)
          # Trigger validation
          _ = template.used_variables
          _ = template.variables
          valid_count += 1
          if verbose:
            self.display.display_success(template_id)
        except ValueError as e:
          invalid_count += 1
          errors.append((template_id, str(e)))
          if verbose:
            self.display.display_error(template_id)
        except Exception as e:
          invalid_count += 1
          errors.append((template_id, f"Load error: {e}"))
          if verbose:
            self.display.display_warning(template_id)
      
      # Summary
      summary_items = {
        "Total templates:": str(total),
        "[green]Valid:[/green]": str(valid_count),
        "[red]Invalid:[/red]": str(invalid_count)
      }
      self.display.display_summary_table("Validation Summary", summary_items)
      
      # Show errors if any
      if errors:
        console.print(f"\n[bold red]Validation Errors:[/bold red]")
        for template_id, error_msg in errors:
          console.print(f"\n[yellow]Template:[/yellow] [cyan]{template_id}[/cyan]")
          console.print(f"[dim]{error_msg}[/dim]")
        raise Exit(code=1)
      else:
        self.display.display_success("All templates are valid!")

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
      context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
    )(module_instance.generate)
    
    # Add defaults commands (simplified - only manage default values)
    defaults_app = Typer(help="Manage default values for template variables")
    defaults_app.command("get", help="Get default value(s)")(module_instance.config_get)
    defaults_app.command("set", help="Set a default value")(module_instance.config_set)
    defaults_app.command("rm", help="Remove a specific default value")(module_instance.config_remove)
    defaults_app.command("clear", help="Clear default value(s)")(module_instance.config_clear)
    defaults_app.command("list", help="Display the config for this module in YAML format")(module_instance.config_list)
    module_app.add_typer(defaults_app, name="defaults")
    
    app.add_typer(module_app, name=cls.name, help=cls.description)
    logger.info(f"Module '{cls.name}' CLI commands registered")

  def _load_template_by_id(self, id: str) -> Template:
    """Load a template by its ID, supporting qualified IDs.
    
    Supports both formats:
    - Simple: "alloy" (uses priority system)
    - Qualified: "alloy.default" (loads from specific library)
    
    Args:
        id: Template ID (simple or qualified)
    
    Returns:
        Template instance
    
    Raises:
        FileNotFoundError: If template is not found
    """
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
      
      # Validate schema version compatibility
      template._validate_schema_version(self.schema_version, self.name)
      
      # If the original ID was qualified, preserve it
      if '.' in id:
        template.id = id
      
      return template
    except Exception as exc:
      logger.error(f"Failed to load template '{id}': {exc}")
      raise FileNotFoundError(f"Template '{id}' could not be loaded: {exc}") from exc

  def _display_template_details(self, template: Template, id: str, show_all: bool = False) -> None:
    """Display template information panel and variables table.
    
    Args:
        template: Template instance to display
        id: Template ID
        show_all: If True, show all variables/sections regardless of needs satisfaction
    """
    self.display.display_template_details(template, id, show_all=show_all)
