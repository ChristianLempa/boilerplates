from abc import ABC
from pathlib import Path
from typing import List, Optional
import logging
from typer import Typer, Option, Argument
from rich.console import Console
from .library import LibraryManager
from .variables import VariableRegistry
from .processor import VariableProcessor

logger = logging.getLogger('boilerplates')


class Module(ABC):
  """Simplified base module with clearer responsibilities."""
  
  # Class attributes set by subclasses
  name: str = None
  description: str = None  
  files: List[str] = None
  
  def __init__(self):
    # Validate required attributes
    if not all([self.name, self.description, self.files]):
      raise ValueError(f"Module {self.__class__.__name__} must define name, description, and files")
    
    self.app = Typer()
    self.libraries = LibraryManager()
    self.variables = VariableRegistry()
    
    # Allow subclasses to initialize their variables
    self._init_variables()
    
  def _init_variables(self):
    """Override in subclasses to register module-specific variables."""
    pass



  def _get_groups_with_template_vars(self, template_vars: List[str]) -> List[str]:
    """Get group names that contain at least one template variable.
    
    Args:
        template_vars: List of variable names used in the template
        
    Returns:
        List of group names that have variables used by the template
    """
    grouped_vars = self.variables.get_variables_for_template(template_vars)
    return list(grouped_vars.keys())



  def list(self):
    """List all templates."""
    templates = self.libraries.find(self.name, self.files, sorted=True)
    for template in templates:
      print(f"{template.id} - {template.name}")
    return templates

  def show(self, id: str = Argument(..., metavar="template", help="The template to show details for")):
    """Show details about a template"""
    logger.debug(f"Showing details for template: {id} in module: {self.name}")

    template = self.libraries.find_by_id(module_name=self.name, files=self.files, template_id=id)
    
    if not template:
      logger.error(f"Template with ID '{id}' not found")
      print(f"Template with ID '{id}' not found.")
      return

    console = Console()
    
    # Build title with version if available
    version_suffix = f" v{template.version}" if template.version else ""
    title = f"[bold magenta]{template.name} ({template.id}{version_suffix})[/bold magenta]"
    
    # Print header
    console.print(title)
    console.print(f"[dim white]{template.description}[/dim white]")
    console.print()
    
    # Build and print metadata fields
    metadata = []
    if template.author:
      metadata.append(f"Author: [cyan]{template.author}[/cyan]")
    if template.date:
      metadata.append(f"Date: [cyan]{template.date}[/cyan]")
    if template.tags:
      metadata.append(f"Tags: [cyan]{', '.join(template.tags)}[/cyan]")
    
    # Find variable groups used by this template
    template_var_groups = self._get_groups_with_template_vars(template.vars)
    
    if template_var_groups:
      metadata.append(f"Functions: [cyan]{', '.join(template_var_groups)}[/cyan]")
    
    # Print all metadata
    for item in metadata:
      console.print(item)
    
    # Template content
    if template.content:
      console.print(f"\n{template.content}")


  def generate(self, id: str = Argument(..., help="Template ID"),
              out: Optional[Path] = Option(None, "--out", "-o")):
    """Generate from template."""
    # Find template
    template = self.libraries.find_by_id(self.name, self.files, id)
    if not template:
      print(f"Template '{id}' not found.")
      return
    
    # Process variables
    processor = VariableProcessor(self.variables)
    values = processor.process(template)
    
    # Render and output
    content = template.render(values)
    
    if out:
      out.parent.mkdir(parents=True, exist_ok=True)
      out.write_text(content)
      print(f"✅ Generated to {out}")
    else:
      print(f"\n{'='*60}\nGenerated Content:\n{'='*60}")
      print(content)
  
  def register_cli(self, app: Typer):
    """Register this module with the CLI app."""
    self.app.command()(self.list)
    self.app.command()(self.show)
    self.app.command()(self.generate)
    app.add_typer(self.app, name=self.name, help=self.description)
