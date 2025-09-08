from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class VariableType(Enum):
  """Supported variable types."""
  STR = "str"
  INT = "int" 
  BOOL = "bool"
  ENUM = "enum"
  FLOAT = "float"


@dataclass
class Variable:
  """Represents a single variable with metadata."""
  
  name: str
  type: VariableType = VariableType.STR
  description: str = ""
  display: str = ""  # Display name for UI
  default: Any = None
  options: List[str] = field(default_factory=list)  # For enum types
  parent: Optional[str] = None  # Parent variable name (for dotted notation)
  
  def has_parent(self) -> bool:
    """Check if this variable has a parent."""
    return self.parent is not None
  
  def get_full_name(self) -> str:
    """Get the full dotted name."""
    if self.parent:
      return f"{self.parent}.{self.name}"
    return self.name


class VariableRegistry:
  """Registry for managing module variables."""
  
  def __init__(self):
    self._variables: Dict[str, Variable] = {}  # Full name -> Variable
  
  def register_variable(self, variable: Variable) -> Variable:
    """Register a variable in the registry."""
    full_name = variable.get_full_name()
    
    # Convert string type to enum if needed
    if isinstance(variable.type, str):
      try:
        variable.type = VariableType(variable.type.lower())
      except ValueError:
        variable.type = VariableType.STR
    
    # Validate enum options
    if variable.type == VariableType.ENUM and not variable.options:
      raise ValueError(f"Variable '{full_name}' of type 'enum' must have options")
    
    self._variables[full_name] = variable
    return variable
  
  def get_variable(self, name: str) -> Optional[Variable]:
    """Get variable by full name."""
    return self._variables.get(name)
  
  def get_all_variables(self) -> Dict[str, Variable]:
    """Get all registered variables."""
    return self._variables.copy()
  
  def get_parent_variables(self) -> List[Variable]:
    """Get all variables that have children (enabler variables)."""
    parent_names = set()
    for var in self._variables.values():
      if var.parent:
        parent_names.add(var.parent)
    
    return [self._variables[name] for name in parent_names if name in self._variables]
  
  def get_children_of(self, parent_name: str) -> List[Variable]:
    """Get all child variables of a specific parent."""
    return [var for var in self._variables.values() if var.parent == parent_name]
  
  def validate_parent_child_relationships(self) -> List[str]:
    """Validate that all parent-child relationships are consistent."""
    errors = []
    
    for var in self._variables.values():
      if var.parent:
        # Check if parent exists
        if var.parent not in self._variables:
          errors.append(f"Variable '{var.get_full_name()}' references non-existent parent '{var.parent}'")
        else:
          parent_var = self._variables[var.parent]
          # Parent should generally be boolean if it has children
          if parent_var.type != VariableType.BOOL:
            errors.append(f"Parent variable '{var.parent}' should be boolean type (has children)")
    
    return errors
