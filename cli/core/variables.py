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
  
  def disable(self) -> None:
    """Disable this variable."""
    self.enabled = False

  def to_dict(self) -> Dict[str, Any]:
    """Convert Variable to dictionary for compatibility with PromptHandler."""
    return {
      'name': self.name,
      'description': self.description,
      'value': self.value,
      'type': self.type,
      'options': self.options,
      'enabled': self.enabled
    }


class VariableGroup():
  """Data class for variable groups."""
  
  def __init__(self, name: str, description: str = "", vars: List[Variable] = None, enabled: bool = True):
    self.name = name
    self.description = description
    self.vars = vars if vars is not None else []
    self.enabled = enabled  # Whether this variable group is enabled
    self.prompt_to_set = ""  # Custom prompt message
    self.prompt_to_enable = ""  # Custom prompt message when asking to enable this group
  
  def disable(self) -> None:
    """Disable this variable group and all its variables."""
    self.enabled = False
    for var in self.vars:
      var.disable()

  def get_all_vars(self) -> List[Variable]:
    """Get all variables in this group."""
    return self.vars

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
  
  def get_all_groups(self) -> List[VariableGroup]:
    """Get all variable groups."""
    return self.variable_groups

  def has_variable(self, name: str) -> bool:
    """Check if a variable exists in any group."""
    for group in self.variable_groups:
      for var in group.vars:
        if var.name == name:
          return True
    return False
  
  def get_variable_value(self, name: str, group_name: str = None) -> Any:
    """Get the value of a variable by name.
    
    Args:
        name: Variable name to find
        group_name: Optional group name to search within
        
    Returns:
        Variable value if found, None otherwise
    """
    for group in self.variable_groups:
      if group_name is not None and group.name != group_name:
        continue
      for var in group.vars:
        if var.name == name:
          return var.value
    return None

  def get_variables_in_template(self, template_vars: List[str]) -> List[tuple]:
    """Get all variables that exist in the template vars list.
    
    Args:
        template_vars: List of variable names used in the template
        
    Returns:
        List of tuples (group_name, variable) for variables found in template
    """
    result = []
    for group in self.variable_groups:
      for var in group.vars:
        if var.name in template_vars:
          result.append((group.name, var))
    return result
