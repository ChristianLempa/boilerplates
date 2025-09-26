from abc import ABC
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from typer import Typer, Option, Argument, Context
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule

from .library import LibraryManager
from .template import Template
from .prompt import PromptHandler
from .args import parse_var_inputs
from .renderers import render_variable_table, render_template_list_table

logger = logging.getLogger(__name__)
console = Console()


class Module(ABC):
  """Streamlined base module that auto-detects variables from templates."""
  
  # Required class attributes for subclasses
  name = None
  description = None  
  files = None
  
  def __init__(self):
    if not all([self.name, self.description, self.files]):
      raise ValueError(
        f"Module {self.__class__.__name__} must define name, description, and files"
      )
    
    logger.info(f"Initializing module '{self.name}'")
    logger.debug(f"Module '{self.name}' configuration: files={self.files}, description='{self.description}'")
    self.libraries = LibraryManager()
    
    # Initialize variables if the subclass defines _init_variables method
    if hasattr(self, '_init_variables'):
      logger.debug(f"Module '{self.name}' has variable initialization method")
      self._init_variables()
    logger.info(f"Module '{self.name}' initialization completed successfully")

  def list(self):
    """List all templates."""
    logger.debug(f"Listing templates for module '{self.name}'")
    templates = []
    module_sections = getattr(self, 'variable_sections', {})

    entries = self.libraries.find(self.name, self.files, sort_results=True)
    for template_dir, library_name in entries:
      template = self._load_template_from_dir(template_dir, library_name, module_sections)
      if template:
        templates.append(template)
    
    if templates:
      logger.info(f"Listing {len(templates)} templates for module '{self.name}'")
      table = render_template_list_table(templates, self.name, include_library=False)
      console.print(table)
    else:
      logger.info(f"No templates found for module '{self.name}'")

    return templates

  def show(
    self,
    id: str,
    show_content: bool = False,
  ):
    """Show template details."""
    logger.debug(f"Showing template '{id}' from module '{self.name}'")
    template = self._load_template_by_id(id)

    header_title = template.name or template.id
    subtitle_parts = [template.id]
    if template.version:
      subtitle_parts.append(f"v{template.version}")
    if template.library:
      subtitle_parts.append(f"library: {template.library}")
    subtitle = " • ".join(subtitle_parts)

    description = template.description or "No description available"
    console.print(Panel(description, title=header_title, subtitle=subtitle, border_style="magenta"))

    metadata_table = Table.grid(padding=(0, 2))
    metadata_table.add_column(style="dim", justify="right")
    metadata_table.add_column(style="white")
    metadata_table.add_row("Author", template.author or "-")
    metadata_table.add_row("Date", template.date or "-")
    metadata_table.add_row("Tags", ", ".join(template.tags) if template.tags else "-")
    metadata_table.add_row("Files", ", ".join(template.files) if template.files else template.file_path.name)
    console.print(Panel(metadata_table, title="Details", border_style="cyan", expand=False))

    if template.variables:
      console.print(render_variable_table(template.variables, sections=template.variable_sections))

    if show_content and template.content:
      console.print(Rule("Template Content"))
      console.print(template.content)


  def generate(
    self,
    id: str = Argument(..., help="Template ID"),
    out: Optional[Path] = Option(None, "--out", "-o"),
    interactive: bool = Option(True, "--interactive/--no-interactive", "-i/-n", help="Enable interactive prompting for variables"),
    var: Optional[List[str]] = Option(None, "--var", "-v", help="Variable override (repeatable). Use KEY=VALUE or --var KEY VALUE"),
    ctx: Context = None,
  ):
    """Generate from template.

    Supports variable overrides via:
      --var KEY=VALUE
      --var KEY VALUE
    """

    logger.info(f"Starting generation for template '{id}' from module '{self.name}'")
    template = self._load_template_by_id(id)

    # Build variable overrides from Typer-collected options and any extra args
    extra_args = []
    try:
      if ctx is not None and hasattr(ctx, "args"):
        extra_args = list(ctx.args)
    except Exception:
      extra_args = []

    cli_overrides = parse_var_inputs(var or [], extra_args)
    if cli_overrides:
      logger.info(f"Received {len(cli_overrides)} variable overrides from CLI")

    # Collect variable values interactively if enabled
    variable_values = {}
    if interactive and template.variables:
      prompt_handler = PromptHandler()
      
      # Collect values with sectioned flow
      collected_values = prompt_handler.collect_variables(
        variables=template.variables,
        template_name=template.name,
        module_name=self.name,
        template_var_order=template.template_var_names,
        module_var_order=template.module_var_names,
        sections=template.variable_sections,
      )
      
      if collected_values:
        variable_values.update(collected_values)
        logger.info(f"Collected {len(collected_values)} variable values from user input")
        
        # Display summary of collected values
        prompt_handler.display_variable_summary(collected_values, template.name)

    # Apply CLI overrides last to take highest precedence
    if cli_overrides:
      variable_values.update(cli_overrides)

    # Render template with collected values
    try:
      variable_values = self._apply_common_defaults(template, variable_values)
      rendered_content = template.render(variable_values)
      logger.info(f"Successfully rendered template '{id}'")
      
      # Output handling
      if out:
        # Write to specified file
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, 'w', encoding='utf-8') as f:
          f.write(rendered_content)
        console.print(f"[green]Generated template to: {out}[/green]")
        logger.info(f"Template written to file: {out}")
      else:
        # Output to stdout
        console.print("[bold blue]Generated Template:[/bold blue]")
        console.print("─" * 50)
        console.print(rendered_content)
        logger.info("Template output to stdout")
        
    except Exception as e:
      logger.error(f"Error rendering template '{id}': {str(e)}")
      console.print(f"[red]Error generating template: {str(e)}[/red]")
      raise

  @classmethod
  def register_cli(cls, app: Typer):
    """Register module commands with the main app using lazy instantiation."""
    logger.debug(f"Registering CLI commands for module '{cls.name}'")

    def _load_module() -> "Module":
      logger.debug(f"Lazily instantiating module '{cls.name}'")
      return cls()

    def _invoke(method_name: str, *args, **kwargs):
      module = _load_module()
      method = getattr(module, method_name)
      return method(*args, **kwargs)

    module_app = Typer()

    @module_app.command()
    def list():
      return _invoke("list")

    @module_app.command()
    def show(
      id: str = Argument(..., help="Template ID"),
      show_content: bool = Option(
        False,
        "--show-content/--hide-content",
        "-c/-C",
        help="Display full template content",
      ),
    ):
      return _invoke("show", id, show_content)

    # Allow extra args so we can parse --var overrides ourselves
    @module_app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
    def generate(
      id: str = Argument(..., help="Template ID"),
      out: Optional[Path] = Option(None, "--out", "-o"),
      interactive: bool = Option(
        True,
        "--interactive/--no-interactive",
        "-i/-n",
        help="Enable interactive prompting for variables",
      ),
      var: Optional[List[str]] = Option(
        None,
        "--var",
        "-v",
        help="Variable override (repeatable). Use KEY=VALUE or --var KEY VALUE",
      ),
      ctx: Context = None,
    ):
      return _invoke(
        "generate",
        id,
        out,
        interactive,
        var,
        ctx,
      )

    app.add_typer(module_app, name=cls.name, help=cls.description)
    logger.info(f"Module '{cls.name}' CLI commands registered")

  def _apply_common_defaults(self, template: Template, values: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure core variables have sensible defaults for non-interactive runs."""
    defaults = {}

    def needs_value(key: str) -> bool:
      if key not in values:
        return True
      current = values[key]
      return current is None or (isinstance(current, str) and current.strip() == "")

    if template.variables.get_variable("service_name") and needs_value("service_name"):
      defaults["service_name"] = template.id

    if template.variables.get_variable("container_name") and needs_value("container_name"):
      defaults["container_name"] = template.id

    if template.variables.get_variable("container_timezone") and needs_value("container_timezone"):
      defaults["container_timezone"] = "UTC"

    if defaults:
      logger.debug(f"Applying common defaults: {defaults}")
      for key, value in defaults.items():
        values[key] = value

    return values

  def _load_template_by_id(self, template_id: str) -> Template:
    result = self.libraries.find_by_id(self.name, self.files, template_id)
    if not result:
      logger.debug(f"Template '{template_id}' not found in module '{self.name}'")
      raise FileNotFoundError(f"Template '{template_id}' not found in module '{self.name}'")

    template_dir, library_name = result
    template = self._load_template_from_dir(
      template_dir,
      library_name,
      getattr(self, 'variable_sections', {}),
    )

    if not template:
      raise FileNotFoundError(f"Template file for '{template_id}' not found in module '{self.name}'")

    return template

  def _load_template_from_dir(
    self,
    template_dir: Path,
    library_name: str,
    module_sections: Dict[str, Any],
  ) -> Optional[Template]:
    template_file = self._resolve_template_file(template_dir)
    if not template_file:
      logger.warning(f"Template directory '{template_dir}' missing expected files {self.files}")
      return None

    try:
      template = Template.from_file(
        template_file,
        module_sections=module_sections,
        library_name=library_name,
      )
      return template
    except Exception as exc:
      logger.error(f"Failed to load template from {template_file}: {exc}")
      return None

  def _resolve_template_file(self, template_dir: Path) -> Optional[Path]:
    for file_name in self.files:
      candidate = template_dir / file_name
      if candidate.exists():
        return candidate
    return None
