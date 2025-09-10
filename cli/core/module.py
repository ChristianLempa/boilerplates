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
    template = self._get_template(id)

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
      print(f"\n{template.content}")

  def _get_template(self, template_id: str):
    """Get template by ID with unified error handling."""
    template = self.libraries.find_by_id(self.name, self.files, template_id)
    
    if not template:
      raise TemplateNotFoundError(template_id, self.name)

    return template

  def generate(
    self,
    id: str = Argument(..., help="Template ID"),
    out: Optional[Path] = Option(None, "--out", "-o")
  ):
    """Generate from template."""
    template = self._get_template(id)
    
    # Validate template (will raise TemplateValidationError if validation fails)
    self._validate_template(template, id)
    
    print("TEST SUCCESSFUL")
  
  def _validate_template(self, template, template_id: str) -> None:
    """Validate template and raise error if validation fails."""
    from .exceptions import TemplateValidationError
    
    validation_errors = []
    
    # Update template variables with module variable registry
    module_variable_registry = getattr(self, 'variables', None)
    if module_variable_registry:
      template.update_variables_with_module_metadata(module_variable_registry)
      
      # Validate parent-child relationships in the registry
      registry_errors = module_variable_registry.validate_parent_child_relationships()
      if registry_errors:
        validation_errors.extend(registry_errors)
      
      # Validate that all template variables are either registered or in template_vars
      unregistered_vars = []
      for var_name in template.vars:
        # Check if variable is registered in module
        if not module_variable_registry.get_variable(var_name):
          # Check if it's defined in template's frontmatter variable_metadata (template_vars)
          if var_name not in template.variable_metadata:
            unregistered_vars.append(var_name)
      
      if unregistered_vars:
        validation_errors.append(
          f"Unregistered variables found: {', '.join(unregistered_vars)}. "
          f"Variables must be either registered in the module or defined in template frontmatter 'variables' section."
        )
    
    # Validate template syntax and structure
    template_warnings = template.validate(module_variable_registry)
    
    # If there are validation errors, fail with TemplateValidationError
    if validation_errors:
      raise TemplateValidationError(template_id, validation_errors)
    
    # If there are non-critical warnings, log them but don't fail
    if template_warnings:
      logger.warning(f"Template '{template_id}' has validation warnings: {template_warnings}")
  
  def register_cli(self, app: Typer):
    """Register module commands with the main app."""
    module_app = Typer()
    module_app.command()(self.list)
    module_app.command()(self.show)
    module_app.command()(self.generate)
    app.add_typer(module_app, name=self.name, help=self.description)
