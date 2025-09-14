from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


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
    logger.debug(f"Attempting to register variable '{full_name}' of type '{variable.type}'")
    
    # Convert string type to enum if needed
    if isinstance(variable.type, str):
      try:
        original_type = variable.type
        variable.type = VariableType(variable.type.lower())
        logger.debug(f"Converted string type '{original_type}' to VariableType.{variable.type.name} for '{full_name}'")
      except ValueError:
        logger.warning(f"Unknown variable type '{variable.type}' for '{full_name}', defaulting to STR")
        variable.type = VariableType.STR
    
    # Validate enum options
    if variable.type == VariableType.ENUM and not variable.options:
      logger.error(f"Variable '{full_name}' of type 'enum' must have options")
      raise ValueError(f"Variable '{full_name}' of type 'enum' must have options")
    
    if variable.type == VariableType.ENUM:
      logger.debug(f"Variable '{full_name}' has {len(variable.options)} enum options: {variable.options}")
    
    if variable.default is not None:
      logger.debug(f"Variable '{full_name}' has default value: {variable.default}")
    
    # Check if already registered
    if full_name in self._variables:
      logger.debug(f"Variable '{full_name}' already registered, replacing")
    
    self._variables[full_name] = variable
    logger.info(f"Registered variable '{full_name}' (type: {variable.type.name}, parent: {variable.parent or 'none'})")
    return variable
  
  def get_variable(self, name: str) -> Optional[Variable]:
    """Get variable by full name."""
    variable = self._variables.get(name)
    if variable:
      logger.debug(f"Retrieved variable '{name}' from registry (type: {variable.type.name})")
    else:
      logger.debug(f"Variable '{name}' not found in registry (available: {list(self._variables.keys())})")
    return variable
  
  def get_all_variables(self) -> Dict[str, Variable]:
    """Get all registered variables."""
    count = len(self._variables)
    if count > 0:
      logger.debug(f"Retrieved {count} variables from registry: {sorted(self._variables.keys())}")
    else:
      logger.debug("No variables registered in registry")
    return self._variables.copy()
  
  def get_parent_variables(self) -> List[Variable]:
    """Get all variables that have children (enabler variables)."""
    parent_names = set()
    for var in self._variables.values():
      if var.parent:
        parent_names.add(var.parent)
    
    parent_vars = [self._variables[name] for name in parent_names if name in self._variables]
    logger.debug(f"Found {len(parent_vars)} parent variables: {sorted(parent_names)}")
    return parent_vars
  
  def get_children_of(self, parent_name: str) -> List[Variable]:
    """Get all child variables of a specific parent."""
    children = [var for var in self._variables.values() if var.parent == parent_name]
    logger.debug(f"Found {len(children)} children for parent '{parent_name}'")
    return children
  
  def validate_parent_child_relationships(self) -> List[str]:
    """Validate that all parent-child relationships are consistent."""
    logger.debug(f"Starting validation of parent-child relationships for {len(self._variables)} variables")
    errors = []
    parent_count = 0
    child_count = 0
    
    for var in self._variables.values():
      if var.parent:
        child_count += 1
        # Check if parent exists
        if var.parent not in self._variables:
          error_msg = f"Variable '{var.get_full_name()}' references non-existent parent '{var.parent}'"
          logger.warning(f"Validation error: {error_msg}")
          errors.append(error_msg)
        else:
          parent_var = self._variables[var.parent]
          # Parent should generally be boolean if it has children
          if parent_var.type != VariableType.BOOL:
            warning_msg = f"Parent variable '{var.parent}' is type '{parent_var.type.name}' but has children"
            logger.warning(f"Validation warning: {warning_msg}")
            errors.append(f"Parent variable '{var.parent}' should be boolean type (has children)")
      else:
        # Count root/parent variables
        children = self.get_children_of(var.name)
        if children:
          parent_count += 1
    
    if errors:
      logger.error(f"Variable registry validation failed with {len(errors)} errors")
      for error in errors:
        logger.debug(f"  - {error}")
    else:
      logger.info(f"Variable registry validation passed ({parent_count} parents, {child_count} children)")
    
    return errors
