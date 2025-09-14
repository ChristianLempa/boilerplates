from abc import ABC
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from typer import Typer, Option, Argument
from rich.console import Console

from .library import LibraryManager

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
    templates = self.libraries.find(self.name, self.files, sorted=True)
    
    if templates:
      logger.info(f"Listing {len(templates)} templates for module '{self.name}'")
    else:
      logger.info(f"No templates found for module '{self.name}'")
    
    # Display templates without enrichment (enrichment only needed for generation)
    for template in templates:
      console.print(f"[cyan]{template.id}[/cyan] - {template.name}")
    
    return templates

  def show(self, id: str = Argument(..., help="Template ID")):
    """Show template details."""
    logger.debug(f"Showing template '{id}' from module '{self.name}'")
    # Get template directly from library without enrichment (not needed for display)
    template = self.libraries.find_by_id(self.name, self.files, id)
    
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
    
    # Variables (show raw template variables without module enrichment)
    if template.vars:
      console.print(f"Variables: [cyan]{', '.join(sorted(template.vars))}[/cyan]")
    
    # Content
    if template.content:
      print(f"\n{template.content}")


  def generate(
    self,
    id: str = Argument(..., help="Template ID"),
    out: Optional[Path] = Option(None, "--out", "-o")
  ):
    """Generate from template."""

    logger.info(f"Starting generation for template '{id}' from module '{self.name}'")
    # Fetch template from library
    template = self.libraries.find_by_id(self.name, self.files, id)
    
    if not template:
      logger.error(f"Template '{id}' not found for generation in module '{self.name}'")
      raise FileNotFoundError(f"Template '{id}' not found in module '{self.name}'")

    # PLACEHOLDER FOR TEMPLATE GENERATION LOGIC

  def register_cli(self, app: Typer):
    """Register module commands with the main app."""
    logger.debug(f"Registering CLI commands for module '{self.name}'")
    module_app = Typer()
    module_app.command()(self.list)
    module_app.command()(self.show)
    module_app.command()(self.generate)
    app.add_typer(module_app, name=self.name, help=self.description)
    logger.info(f"Module '{self.name}' CLI commands registered")
