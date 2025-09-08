from abc import ABC
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
import yaml
from typer import Typer, Option, Argument
from rich.console import Console
from .config import get_config
from .exceptions import TemplateNotFoundError, TemplateValidationError
from .library import LibraryManager
from .prompt import SimplifiedPromptHandler

logger = logging.getLogger('boilerplates')
console = Console()  # Single shared console instance


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
    
    # Process variables and render
    values = self._process_variables(template)
    
    try:
      content = template.render(values)
    except Exception as e:
      logger.error(f"Failed to render template: {e}")
      raise
    
    # Output result
    if out:
      out.parent.mkdir(parents=True, exist_ok=True)
      out.write_text(content)
      console.print(f"[green]✅ Generated to {out}[/green]")
    else:
      console.print(f"\n{'='*60}\nGenerated Content:\n{'='*60}")
      console.print(content)
  
  def _validate_template(self, template, template_id: str) -> None:
    """Validate template and raise error if validation fails."""
    # Template is now self-validating, no need for registered variables
    warnings = template.validate()
    
    # If there are non-critical warnings, log them but don't fail
    if warnings:
      logger.warning(f"Template '{template_id}' has validation warnings: {warnings}")
  
  def _process_variables(self, template) -> Dict[str, Any]:
    """Process template variables with prompting."""
    # Use template's analyzed variables
    if not template.variables:
      return {}
    
    # Apply metadata to variables
    self._apply_metadata_to_variables(template.variables, template.variable_metadata)
    
    # Collect defaults from analyzed variables
    defaults = {}
    for var_name, var in template.variables.items():
      if var.default is not None:
        defaults[var_name] = var.default
    
    # Use rich output if enabled
    if not get_config().use_rich_output:
      # Simple fallback - just prompt for missing values
      values = defaults.copy()
      for var_name, var in template.variables.items():
        if var_name not in values:
          values[var_name] = input(f"Enter {var_name}: ")
      return values
    
    # Pass metadata to prompt handler
    prompt_handler = SimplifiedPromptHandler(template.variables)
    prompt_handler.category_metadata = self.metadata.get('categories', {})
    return prompt_handler()
  
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
