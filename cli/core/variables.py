from typing import Any, Dict, List, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict


@dataclass
class Variable:
  """Variable with automatic grouping via dotted notation.
  
  Variables are automatically grouped by their prefix:
  - 'traefik' is a standalone boolean (enabler)
  - 'traefik.host' is part of the traefik group
  - 'port.http' is part of the port group
  
  Type can be:
  - 'string': String value (default)
  - 'integer': Integer value  
  - 'float': Float value
  - 'boolean': Boolean value
  """
  name: str
  description: str = ""
  default: Any = None
  type: str = "string"  # string, integer, float, boolean
  
  def to_prompt_config(self) -> Dict[str, Any]:
    """Convert to prompt configuration."""
    return {
      'name': self.name,
      'description': self.description, 
      'type': self.type,
      'default': self.default
    }


class VariableRegistry:
  """Simplified variable registry with automatic grouping via dotted notation."""
  
  def __init__(self):
    self.variables: Dict[str, Variable] = OrderedDict()
  
  def register(self, var: Variable) -> None:
    """Register a variable."""
    self.variables[var.name] = var
  
  def get_variables_for_template(self, template_vars: List[str]) -> Dict[str, Variable]:
    """Get variables that are used in the template.
    
    Returns a dict of variable name to Variable object for all
    variables used in the template, preserving registration order.
    """
    result = OrderedDict()
    # Iterate through registered variables to preserve registration order
    for var_name in self.variables.keys():
      if var_name in template_vars:
        result[var_name] = self.variables[var_name]
    return result
  
  def group_variables(self, variables: Dict[str, Variable]) -> Tuple[Dict[str, List[str]], List[str]]:
    """Automatically group variables by their dotted notation prefix.
    
    Returns:
      (groups, standalone) where:
      - groups: Dict mapping group name to list of variable names in that group
      - standalone: List of variable names that aren't in any group
    """
    groups = OrderedDict()
    standalone = []
    all_var_names = list(variables.keys())
    
    for var_name in all_var_names:
      if '.' in var_name:
        # This is a grouped variable like 'traefik.host'
        prefix = var_name.split('.')[0]
        if prefix not in groups:
          groups[prefix] = []
        groups[prefix].append(var_name)
      else:
        # Check if this is a group parent (has children)
        is_group_parent = any(v.startswith(f"{var_name}.") for v in all_var_names)
        if is_group_parent:
          if var_name not in groups:
            groups[var_name] = []
          # The parent itself is not added to the group list, it's the enabler
        else:
          # Truly standalone variable
          standalone.append(var_name)
    
    return groups, standalone
