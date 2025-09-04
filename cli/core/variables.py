from typing import Any, Dict, List, Tuple
from .config import ConfigManager


class Variable:
  """Data class for variable information."""
  
  def __init__(self, name: str, description: str = "", value: Any = None, var_type: str = "string", options: List[Any] = None, enabled: bool = True):
    self.name = name
    self.description = description
    self.value = value
    self.type = var_type  # e.g., string, integer, boolean, choice
    self.options = options if options is not None else []  # For choice type
    self.enabled = enabled  # Whether this variable is enabled (default: True)


class VariableGroup():
  """Data class for variable groups."""
  
  def __init__(self, name: str, description: str = "", vars: List[Variable] = None, enabled: bool = True):
    self.name = name
    self.description = description
    self.vars = vars if vars is not None else []
    self.enabled = enabled  # Whether this variable group is enabled
    self.prompt_to_set = ""  # Custom prompt message
    self.prompt_to_enable = ""  # Custom prompt message when asking to enable this group
  
  def is_enabled(self) -> bool:
    """Check if this variable group is enabled."""
    return self.enabled
  
  def enable(self) -> None:
    """Enable this variable group."""
    self.enabled = True
  
  def disable(self) -> None:
    """Disable this variable group."""
    self.enabled = False
  
  def get_enabled_variables(self) -> List[Variable]:
    """Get all enabled variables in this group."""
    return [var for var in self.vars if var.enabled]
  
  def disable_variables_not_in_template(self, template_vars: List[str]) -> None:
    """Disable all variables that are not found in the template variables.
    
    Args:
        template_vars: List of variable names used in the template
    """
    for var in self.vars:
      if var.name not in template_vars:
        var.enabled = False
  
  @classmethod
  def from_dict(cls, name: str, config: Dict[str, Any]) -> "VariableGroup":
    """Create a VariableGroup from a dictionary configuration."""
    variables = []
    vars_config = config.get("vars", {})
    
    for var_name, var_config in vars_config.items():
      var_type = var_config.get("var_type", "string")  # Default to string if not specified
      enabled = var_config.get("enabled", True)  # Default to enabled if not specified
      variables.append(Variable(
        name=var_name,
        description=var_config.get("description", ""),
        value=var_config.get("value"),
        var_type=var_type,
        enabled=enabled
      ))
    
    return cls(
      name=name,
      description=config.get("description", ""),
      vars=variables,
      enabled=config.get("enabled", True)  # Default to enabled if not specified
    )


class VariableManager:
  """Manager class for handling collections of VariableGroups.
  
  The VariableManager centralizes variable-related operations for:
  - Managing VariableGroups
  - Validating template variables
  - Filtering variables for specific templates
  - Resolving variable defaults with priority handling
  """
  
  def __init__(self, variable_groups: List[VariableGroup] = None, config_manager: ConfigManager = None):
    """Initialize the VariableManager with a list of VariableGroups and ConfigManager."""
    self.variable_groups = variable_groups if variable_groups is not None else []
    self.config_manager = config_manager if config_manager is not None else ConfigManager()
  
  def add_group(self, group: VariableGroup) -> None:
    """Add a VariableGroup to the manager."""
    if not isinstance(group, VariableGroup):
      raise ValueError("group must be a VariableGroup instance")
    self.variable_groups.append(group)
  
  def disable_variables_not_in_template(self, template_vars: List[str]) -> None:
    """Disable all variables in all groups that are not found in the template variables.
    
    Args:
        template_vars: List of variable names used in the template
    """
    for group in self.variable_groups:
      group.disable_variables_not_in_template(template_vars)
  
  def get_all_variable_names(self) -> List[str]:
    """Get all variable names from all variable groups."""
    return [var.name for group in self.variable_groups for var in group.vars]
  
  def has_variable(self, name: str) -> bool:
    """Check if a variable exists in any group."""
    for group in self.variable_groups:
      for var in group.vars:
        if var.name == name:
          return True
    return False
  
  def validate_template_variables(self, template_vars: List[str]) -> Tuple[bool, List[str]]:
    """Validate if all template variables exist in the variable groups.
    
    Args:
        template_vars: List of variable names used in the template
        
    Returns:
        Tuple of (success: bool, missing_variables: List[str])
    """
    all_variables = self.get_all_variable_names()
    missing_variables = [var for var in template_vars if var not in all_variables]
    success = len(missing_variables) == 0
    return success, missing_variables
  
  def filter_variables_for_template(self, template_vars: List[str]) -> Dict[str, Any]:
    """Filter the variable groups to only include variables needed by the template.
    
    Args:
        template_vars: List of variable names used in the template
        
    Returns:
        Dictionary with filtered variable groups and their variables, including group metadata
    """
    filtered_vars = {}
    
    for group in self.variable_groups:
      group_has_template_vars = False
      group_vars = {}
      
      for variable in group.vars:
        if variable.name in template_vars:
          group_has_template_vars = True
          group_vars[variable.name] = {
            'name': variable.name,
            'description': variable.description,
            'value': variable.value,
            'type': variable.type,
            'options': getattr(variable, 'options', []),
            'enabled': variable.enabled
          }
      
      # Only include groups that have variables used by the template
      if group_has_template_vars:
        filtered_vars[group.name] = {
          'description': group.description,
          'enabled': group.enabled,
          'prompt_to_set': getattr(group, 'prompt_to_set', ''),
          'prompt_to_enable': getattr(group, 'prompt_to_enable', ''),
          'vars': group_vars
        }
    
    return filtered_vars
  
  def get_module_defaults(self, template_vars: List[str]) -> Dict[str, Any]:
    """Get default values from module variable definitions for template variables.
    
    Args:
        template_vars: List of variable names used in the template
        
    Returns:
        Dictionary mapping variable names to their default values
    """
    defaults = {}
    
    for group in self.variable_groups:
      for variable in group.vars:
        if variable.name in template_vars and variable.value is not None:
          defaults[variable.name] = variable.value
    
    return defaults
  
  def resolve_variable_defaults(self, module_name: str, template_vars: List[str], template_defaults: Dict[str, Any] = None) -> Dict[str, Any]:
    """Resolve variable default values with hardcoded priority handling.
    
    Priority order (hardcoded):
    1. Module variable defaults (low priority)
    2. Template's built-in defaults from |default() filters (medium priority)
    3. User config defaults (high priority)
    
    Args:
        module_name: Name of the module (for config lookup)
        template_vars: List of variable names used in the template
        template_defaults: Dictionary of template's built-in default values
        
    Returns:
        Dictionary of variable names to their resolved default values
    """
    if template_defaults is None:
      template_defaults = {}
    
    # Priority 1: Start with module variable defaults (low priority)
    defaults = self.get_module_defaults(template_vars)
    
    # Priority 2: Override with template's built-in defaults (medium priority)
    defaults.update(template_defaults)
    
    # Priority 3: Override with user config defaults (high priority)
    user_config_defaults = self.config_manager.get_variable_defaults(module_name)
    for var_name in template_vars:
      if var_name in user_config_defaults:
        defaults[var_name] = user_config_defaults[var_name]
    
    return defaults
  
  def get_summary(self) -> Dict[str, Any]:
    """Get a summary of all variable groups and their contents."""
    summary = {
      'total_groups': len(self.variable_groups),
      'total_variables': len(self.get_all_variable_names()),
      'groups': []
    }
    
    for group in self.variable_groups:
      group_info = {
        'name': group.name,
        'description': group.description,
        'variable_count': len(group.vars),
        'variables': [var.name for var in group.vars]
      }
      summary['groups'].append(group_info)
    
    return summary
