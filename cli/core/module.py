from abc import ABC
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from typer import Typer, Option, Argument
from rich.console import Console
from .config import get_config
from .exceptions import TemplateNotFoundError, TemplateValidationError
from .library import LibraryManager
from .prompt import PromptHandler
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
    
    # Variable groups
    if template.vars:
      groups = self.variables.get_variables_for_template(template.vars)
      if groups:
        console.print(f"Functions: [cyan]{', '.join(groups.keys())}[/cyan]")
    
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
    errors = template.validate(set(self.variables.variables.keys()))
    
    if errors:
      logger.error(f"Template '{template_id}' validation failed")
      raise TemplateValidationError(template_id, errors)
  
  def _process_variables(self, template) -> Dict[str, Any]:
    """Process template variables with prompting."""
    grouped_vars = self.variables.get_variables_for_template(list(template.vars))
    if not grouped_vars:
      return {}
    
    # Collect all defaults
    defaults = {
      var.name: var.default 
      for group_vars in grouped_vars.values() 
      for var in group_vars 
      if var.default is not None
    }
    defaults.update(template.var_defaults)  # Template defaults override
    
    # Use rich output if enabled
    if not get_config().use_rich_output:
      # Simple fallback - just prompt for missing values
      values = defaults.copy()
      for group_vars in grouped_vars.values():
        for var in group_vars:
          if var.name not in values:
            desc = f" ({var.description})" if var.description else ""
            values[var.name] = input(f"Enter {var.name}{desc}: ")
      return values
    
    # Format for PromptHandler
    formatted_groups = {}
    for group_name, variables in grouped_vars.items():
      group_info = self.variables.groups.get(group_name, {})
      formatted_groups[group_name] = {
        'display_name': group_info.get('display_name', group_name.title()),
        'description': group_info.get('description', ''),
        'icon': group_info.get('icon', ''),
        'vars': {},
        'enabler': self.variables.group_enablers.get(group_name, '')
      }
      
      # Add usage patterns to each variable config
      for var in variables:
        var_config = var.to_prompt_config()
        # Add usage patterns if this variable is used in the template
        if var.name in template.var_usage:
          var_config['usage_patterns'] = template.var_usage[var.name]
        formatted_groups[group_name]['vars'][var.name] = var_config
    
    return PromptHandler(formatted_groups, defaults)()
  
  def register_cli(self, app: Typer):
    """Register module commands with the main app."""
    module_app = Typer()
    module_app.command()(self.list)
    module_app.command()(self.show)
    module_app.command()(self.generate)
    app.add_typer(module_app, name=self.name, help=self.description)
