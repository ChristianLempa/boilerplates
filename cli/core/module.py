from abc import ABC
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from typer import Typer, Option, Argument, Context
from rich.console import Console

from .library import LibraryManager
from .template import Template
from .prompt import PromptHandler
from .args import parse_var_inputs

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
    
    self.metadata = self._build_metadata()
    logger.info(f"Module '{self.name}' initialization completed successfully")
  
  def _build_metadata(self) -> Dict[str, Any]:
    """Build metadata from class attributes."""
    metadata = {}
    
    # Add categories if defined
    if hasattr(self, 'categories'):
      metadata['categories'] = self.categories
    
    # Add variable metadata if defined
    if hasattr(self, 'variable_metadata'):
      metadata['variables'] = self.variable_metadata
    
    return metadata

  def list(self):
    """List all templates."""
    logger.debug(f"Listing templates for module '{self.name}'")
    templates = self.libraries.load_templates(
      self.name, 
      self.files, 
      sort_results=True,
      module_variables=getattr(self, 'variables_spec', {})
    )
    
    if templates:
      logger.info(f"Listing {len(templates)} templates for module '{self.name}'")
      for template in templates:
        console.print(f"[cyan]{template.id}[/cyan] - {template.name}")
    else:
      logger.info(f"No templates found for module '{self.name}'")
    
    return templates

  def show(self, id: str = Argument(..., help="Template ID")):
    """Show template details."""
    logger.debug(f"Showing template '{id}' from module '{self.name}'")
    template = self.libraries.load_template_by_id(
      self.name, 
      self.files, 
      id,
      module_variables=getattr(self, 'variables_spec', {})
    )
    
    if not template:
      logger.debug(f"Template '{id}' not found in module '{self.name}'")
      raise FileNotFoundError(f"Template '{id}' not found in module '{self.name}'")

    # Header
    version = f" v{template.version}" if template.version else ""
    console.print(f"[bold magenta]{template.name} ({template.id}{version})[/bold magenta]")
    console.print(f"[dim white]{template.description}[/dim white]\n")
    
    # Metadata (only print if exists)
    metadata = [
      ("Author", template.author),
      ("Date", template.date),
      ("Tags", ', '.join(template.tags) if template.tags else None)
    ]
    
    for label, value in metadata:
      if value:
        console.print(f"{label}: [cyan]{value}[/cyan]")
    
    # Variables (show template variables)
    if template.variables:
      console.print(f"Variables: [cyan]{', '.join(template.variables.get_variable_names())}[/cyan]")
    
    # Content
    if template.content:
      print(f"\n{template.content}")


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
    template = self.libraries.load_template_by_id(
      self.name, 
      self.files, 
      id,
      module_variables=getattr(self, 'variables_spec', {})
    )
    
    if not template:
      logger.error(f"Template '{id}' not found for generation in module '{self.name}'")
      raise FileNotFoundError(f"Template '{id}' not found in module '{self.name}'")

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

  def register_cli(self, app: Typer):
    """Register module commands with the main app."""
    logger.debug(f"Registering CLI commands for module '{self.name}'")
    module_app = Typer()
    module_app.command()(self.list)
    module_app.command()(self.show)
    # Allow extra args so we can parse --var overrides ourselves
    module_app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})(self.generate)
    app.add_typer(module_app, name=self.name, help=self.description)
    logger.info(f"Module '{self.name}' CLI commands registered")
