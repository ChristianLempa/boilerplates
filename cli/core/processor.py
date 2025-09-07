from typing import Any, Dict, List
import logging
from .variables import VariableRegistry
from .template import Template
from .prompt import PromptHandler

logger = logging.getLogger('boilerplates')


class VariableProcessor:
  """Variable processor for template generation."""
  
  def __init__(self, variable_registry: VariableRegistry):
    self.registry = variable_registry
  
  def process(self, template: Template) -> Dict[str, Any]:
    """Process variables for a template."""
    
    # Get variables needed by template
    grouped_vars = self.registry.get_variables_for_template(template.vars)
    
    if not grouped_vars:
      return {}
    
    # Convert to format expected by PromptHandler
    formatted_groups = {}
    for group_name, variables in grouped_vars.items():
      group_info = self.registry.groups.get(group_name, {
        'display_name': group_name.title(),
        'description': '',
        'icon': ''
      })
      
      # Convert variables to dict format expected by PromptHandler
      vars_dict = {}
      for var in variables:
        vars_dict[var.name] = var.to_prompt_config()
      
      formatted_groups[group_name] = {
        'display_name': group_info['display_name'],
        'description': group_info['description'],
        'icon': group_info['icon'],
        'vars': vars_dict,
        'enabler': self.registry.group_enablers.get(group_name, '')
      }
    
    # Resolve defaults (template defaults override variable defaults)
    defaults = {}
    for group_vars in grouped_vars.values():
      for var in group_vars:
        if var.default is not None:
          defaults[var.name] = var.default
    
    # Template defaults have higher priority
    defaults.update(template.var_defaults)
    
    # Prompt for values using the PromptHandler
    prompt = PromptHandler(formatted_groups, defaults)
    return prompt()  # Call the handler directly
