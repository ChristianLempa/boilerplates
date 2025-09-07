from typing import Any, Dict, List
from dataclasses import dataclass, field
from collections import OrderedDict


@dataclass
class Variable:
  """Variable with all necessary properties."""
  name: str
  description: str = ""
  default: Any = None
  type: str = "string"
  options: List[Any] = field(default_factory=list)
  group: str = "general"
  required: bool = False
  
  def to_prompt_config(self) -> Dict[str, Any]:
    """Convert to prompt configuration."""
    return {
      'name': self.name,
      'description': self.description, 
      'type': self.type,
      'options': self.options,
      'required': self.required,
      'default': self.default
    }


class VariableRegistry:
  """Variable management for modules."""
  
  def __init__(self):
    self.variables: Dict[str, Variable] = OrderedDict()
    self.groups: Dict[str, Dict[str, Any]] = OrderedDict()
    self.registration_order: Dict[str, List[str]] = {}  # group -> ordered list of variable names
    self.group_enablers: Dict[str, str] = {}  # group -> enabler variable name
  
  def register_variable(self, var: Variable) -> None:
    """Register a variable."""
    self.variables[var.name] = var
    # Track registration order per group
    if var.group not in self.registration_order:
      self.registration_order[var.group] = []
    self.registration_order[var.group].append(var.name)
    
  def register_group(self, name: str, display_name: str, 
                    description: str = "", icon: str = "", enabler: str = "") -> None:
    """Register a variable group.
    
    Args:
        name: Internal group name
        display_name: Display name for the group
        description: Group description
        icon: Optional icon for the group
        enabler: Optional variable name that controls if this group is enabled
    """
    self.groups[name] = {
      'display_name': display_name,
      'description': description,
      'icon': icon
    }
    
    if enabler:
      self.group_enablers[name] = enabler
  
  def get_variables_for_template(self, template_vars: List[str]) -> Dict[str, List[Variable]]:
    """Get variables grouped by their group name, preserving registration order."""
    grouped = OrderedDict()
    
    # First, organize variables by group
    temp_grouped = {}
    for var_name in template_vars:
      if var_name in self.variables:
        var = self.variables[var_name]
        if var.group not in temp_grouped:
          temp_grouped[var.group] = []
        temp_grouped[var.group].append(var)
    
    # Then, sort variables within each group by registration order
    for group_name, vars_list in temp_grouped.items():
      grouped[group_name] = sorted(
        vars_list,
        key=lambda v: self.registration_order.get(group_name, []).index(v.name) 
        if v.name in self.registration_order.get(group_name, []) else float('inf')
      )
    
    return grouped
