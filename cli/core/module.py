from abc import ABC
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import yaml
from typer import Typer, Option, Argument
from rich.console import Console
from .exceptions import TemplateNotFoundError
from .library import LibraryManager

logger = logging.getLogger('boilerplates')
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
    
    self.libraries = LibraryManager()
    
    # Initialize variables if the subclass defines _init_variables method
    if hasattr(self, '_init_variables'):
      self._init_variables()
    
    self.metadata = self._build_metadata()
  
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
    templates = self.libraries.find(self.name, self.files, sorted=True)
    for template in templates:
      console.print(f"[cyan]{template.id}[/cyan] - {template.name}")
    return templates

  def show(self, id: str = Argument(..., help="Template ID")):
    """Show template details."""
    logger.debug(f"Showing template: {id}")
    
    template = self._get_template(id)
    if not template:
      return
    
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
    
    # Variables
    if template.vars:
      console.print(f"Variables: [cyan]{', '.join(sorted(template.vars))}[/cyan]")
    
    # Content
    if template.content:
      console.print(f"\n{template.content}")
  
  def _get_template(self, template_id: str, raise_on_missing: bool = False):
    """Get template by ID with unified error handling."""
    template = self.libraries.find_by_id(self.name, self.files, template_id)
    
    if not template:
      logger.error(f"Template '{template_id}' not found")
      if raise_on_missing:
        raise TemplateNotFoundError(template_id, self.name)
      console.print(f"[red]Template '{template_id}' not found[/red]")
    
    return template

  def generate(
    self,
    id: str = Argument(..., help="Template ID"),
    out: Optional[Path] = Option(None, "--out", "-o")
  ):
    """Generate from template."""
    logger.debug(f"Generating template: {id}")
    
    template = self._get_template(id, raise_on_missing=True)
    
    # Validate template (will raise TemplateValidationError if validation fails)
    self._validate_template(template, id)
    
    print("TEST")
  
  def _validate_template(self, template, template_id: str) -> None:
    """Validate template and raise error if validation fails."""
    # Update template variables with module variable registry
    module_variable_registry = getattr(self, 'variables', None)
    if module_variable_registry:
      template.update_variables_with_module_metadata(module_variable_registry)
      
      # Validate parent-child relationships in the registry
      registry_errors = module_variable_registry.validate_parent_child_relationships()
      if registry_errors:
        logger.error(f"Variable registry validation errors: {registry_errors}")
    
    # Validate template with module variables
    warnings = template.validate(module_variable_registry)
    
    # If there are non-critical warnings, log them but don't fail
    if warnings:
      logger.warning(f"Template '{template_id}' has validation warnings: {warnings}")
  
  def _apply_metadata_to_variables(self, variables: Dict[str, Any], template_metadata: Dict[str, Any]):
    """Apply metadata from module and template to variables."""
    # First apply module metadata
    module_var_metadata = self.metadata.get('variables', {})
    for var_name, var in variables.items():
      if var_name in module_var_metadata:
        meta = module_var_metadata[var_name]
        if 'hint' in meta and not var.hint:
          var.hint = meta['hint']
        if 'description' in meta and not var.description:
          var.description = meta['description']
        if 'tip' in meta and not var.tip:
          var.tip = meta['tip']
        if 'validation' in meta and not var.validation:
          var.validation = meta['validation']
        if 'icon' in meta and not var.icon:
          var.icon = meta['icon']
    
    # Then apply template metadata (overrides module metadata)
    for var_name, var in variables.items():
      if var_name in template_metadata:
        meta = template_metadata[var_name]
        if 'hint' in meta:
          var.hint = meta['hint']
        if 'description' in meta:
          var.description = meta['description']
        if 'tip' in meta:
          var.tip = meta['tip']
        if 'validation' in meta:
          var.validation = meta['validation']
        if 'icon' in meta:
          var.icon = meta['icon']
  
  def register_cli(self, app: Typer):
    """Register module commands with the main app."""
    module_app = Typer()
    module_app.command()(self.list)
    module_app.command()(self.show)
    module_app.command()(self.generate)
    app.add_typer(module_app, name=self.name, help=self.description)
