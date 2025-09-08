from abc import ABC
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from typer import Typer, Option, Argument
from rich.console import Console
from .config import get_config
from .exceptions import TemplateNotFoundError, TemplateValidationError
from .library import LibraryManager
from .prompt import SimplifiedPromptHandler
from .variables import VariableRegistry

logger = logging.getLogger('boilerplates')
console = Console()  # Single shared console instance


class Module(ABC):
  """Streamlined base module with minimal redundancy."""
  
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
    self.variables = VariableRegistry()
    
    # Allow subclasses to initialize variables if they override this
    if hasattr(self, '_init_variables'):
      self._init_variables()


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
    # Get registered variables for validation
    registered_vars = set(self.variables.variables.keys())
    
    # Validate will raise TemplateValidationError for critical errors (syntax)
    # and return a list of warnings for non-critical issues
    warnings = template.validate(registered_vars)
    
    # If there are non-critical warnings, log them but don't fail
    if warnings:
      logger.warning(f"Template '{template_id}' has validation warnings: {warnings}")
      # Optionally, you could still raise an error for strict validation:
      # raise TemplateValidationError(template_id, warnings)
  
  def _process_variables(self, template) -> Dict[str, Any]:
    """Process template variables with prompting."""
    # Get variables used in template that are registered
    template_vars = self.variables.get_variables_for_template(list(template.vars))
    if not template_vars:
      return {}
    
    # Collect all defaults from variables and template
    defaults = {}
    for var_name, var in template_vars.items():
      if var.default is not None:
        defaults[var_name] = var.default
    
    # Handle dict variable defaults specially
    # Auto-detect dict type from template usage
    for var_name, var in template_vars.items():
      # If template uses dict access, treat it as dict type regardless of registration
      if var_name in template.var_dict_keys:
        # This is a dict variable with dynamic keys
        # Get defaults for each key from template
        if var_name in template.var_defaults and isinstance(template.var_defaults[var_name], dict):
          if var_name not in defaults:
            defaults[var_name] = {}
          defaults[var_name].update(template.var_defaults[var_name])
    
    # Also add template defaults for regular variables
    for k, v in template.var_defaults.items():
      if not isinstance(v, dict):  # Skip dict defaults, already handled
        defaults[k] = v
    
    # Use rich output if enabled
    if not get_config().use_rich_output:
      # Simple fallback - just prompt for missing values
      values = defaults.copy()
      for var_name, var in template_vars.items():
        if var_name not in values:
          desc = f" ({var.description})" if var.description else ""
          values[var_name] = input(f"Enter {var_name}{desc}: ")
      return values
    
    # Pass dict keys info to prompt handler
    # Use the new simplified prompt handler with dict support
    return SimplifiedPromptHandler(template_vars, defaults, template.var_dict_keys)()
  
  def register_cli(self, app: Typer):
    """Register module commands with the main app."""
    module_app = Typer()
    module_app.command()(self.list)
    module_app.command()(self.show)
    module_app.command()(self.generate)
    app.add_typer(module_app, name=self.name, help=self.description)
