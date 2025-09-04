from typing import Any, Dict, List
import logging
from .variables import VariableManager
from .config import ConfigManager
from .template import Template
from .prompt import PromptHandler

logger = logging.getLogger('boilerplates')


class VariableProcessor:
  """
  Handles the complete variable population pipeline for template generation.
  
  This class implements a clean, step-by-step approach to:
  1. Filter variables relevant to the template
  2. Resolve defaults with proper priority handling  
  3. Prompt users for missing values
  4. Return final variable values for template rendering
  """
  
  def __init__(self, vars_manager: VariableManager, config_manager: ConfigManager, module_name: str = None):
    """Initialize the processor with required managers."""
    self.vars = vars_manager
    self.config = config_manager
    self.module_name = module_name
    self.logger = logging.getLogger('boilerplates')
  
  def process_variables_for_template(self, template: Template) -> Dict[str, Any]:
    """
    Execute the complete variable processing pipeline.
    
    Args:
        template: Template object containing variables and defaults
        
    Returns:
        Dictionary of final variable values ready for template rendering
    """
    self.logger.debug("Starting variable processing pipeline")
    
    # Step 1: Filter and prepare variables for this template
    self._prepare_variables_for_template(template)
    
    # Step 2: Resolve defaults in priority order
    resolved_defaults = self._resolve_defaults(template)
    
    # Step 3: Handle user interaction and prompting
    final_values = self._prompt_for_values(template, resolved_defaults)
    
    self.logger.debug(f"Variable processing completed with {len(final_values)} variables")
    return final_values
  
  def _prepare_variables_for_template(self, template: Template) -> None:
    """
    Step 1: Disable variables not needed by the template.
    
    This optimizes the user experience by only showing relevant variables.
    """
    self.logger.debug(f"Filtering variables for template with {len(template.vars)} required variables")
    
    disabled_count = 0
    for var_group in self.vars.get_all_groups():
      for var in var_group.get_all_vars():
        if var.name not in template.vars:
          var.disable()
          disabled_count += 1
    
    self.logger.debug(f"Disabled {disabled_count} variables not needed by template")
  
  def _resolve_defaults(self, template: Template) -> Dict[str, Any]:
    """
    Step 2: Resolve variable defaults with proper priority handling.
    
    Priority order (low to high):
    1. Module variable defaults
    2. Template built-in defaults 
    3. User configuration defaults
    
    Returns:
        Dictionary of resolved default values
    """
    self.logger.debug("Resolving variable defaults with priority handling")
    defaults = {}
    
    # Priority 1: Module variable defaults (lowest priority)
    for group in self.vars.get_all_groups():
      for var in group.get_all_vars():
        if var.name in template.vars and var.value is not None:
          defaults[var.name] = var.value
          self.logger.debug(f"Set module default for '{var.name}': {var.value}")
    
    # Priority 2: Template defaults (medium priority)
    for var_name, default_value in template.var_defaults.items():
      if var_name in template.vars:
        defaults[var_name] = default_value
        self.logger.debug(f"Set template default for '{var_name}': {default_value}")
    
    # Priority 3: User config defaults (highest priority)
    user_defaults = self.config.get_variable_defaults(self.module_name or "unknown")
    for var_name, default_value in user_defaults.items():
      if var_name in template.vars:
        defaults[var_name] = default_value
        self.logger.debug(f"Set user config default for '{var_name}': {default_value}")
    
    self.logger.debug(f"Resolved {len(defaults)} default values")
    return defaults
  
  def _prompt_for_values(self, template: Template, defaults: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 3: Handle user prompting for variable values.
    
    Args:
        template: Template object
        defaults: Resolved default values
        
    Returns:
        Dictionary of final variable values
    """
    self.logger.debug("Starting user prompting phase")
    
    # Filter variable groups to only include those needed by the template
    filtered_groups = self._filter_variables_for_template(template.vars)
    
    # Create and execute prompt handler
    prompt_handler = PromptHandler(filtered_groups, defaults)
    final_values = prompt_handler()
    
    self.logger.debug(f"User prompting completed with {len(final_values)} final values")
    return final_values
  
  def _filter_variables_for_template(self, template_vars: List[str]) -> Dict[str, Any]:
    """
    Filter variable groups to only include variables needed by the template.
    
    This is adapted from the existing method in the Module class.
    """
    filtered_vars = {}
    template_vars_set = set(template_vars)  # Convert to set for O(1) lookup
    
    for group in self.vars.get_all_groups():
      # Only process enabled groups
      if not group.enabled:
        continue
        
      # Get variables that match template vars and are enabled
      group_vars = {
        var.name: var.to_dict() 
        for var in group.vars 
        if var.name in template_vars_set and var.enabled
      }
      
      # Only include groups that have variables
      if group_vars:
        filtered_vars[group.name] = {
          'description': group.description,
          'enabled': group.enabled,
          'prompt_to_set': getattr(group, 'prompt_to_set', ''),
          'prompt_to_enable': getattr(group, 'prompt_to_enable', ''),
          'vars': group_vars
        }
    
    self.logger.debug(f"Filtered to {len(filtered_vars)} variable groups for template")
    return filtered_vars
