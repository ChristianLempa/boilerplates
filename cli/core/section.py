from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, List, Optional

from .variable import Variable


class VariableSection:
  """Groups variables together with shared metadata for presentation."""

  def __init__(self, data: dict[str, Any]) -> None:
    """Initialize VariableSection from a dictionary.
    
    Args:
        data: Dictionary containing section specification with required 'key' and 'title' keys
    """
    if not isinstance(data, dict):
      raise ValueError("VariableSection data must be a dictionary")
    
    if "key" not in data:
      raise ValueError("VariableSection data must contain 'key'")
    
    if "title" not in data:
      raise ValueError("VariableSection data must contain 'title'")
    
    self.key: str = data["key"]
    self.title: str = data["title"]
    self.variables: OrderedDict[str, Variable] = OrderedDict()
    self.description: Optional[str] = data.get("description")
    self.toggle: Optional[str] = data.get("toggle")
    # Track which fields were explicitly provided (to support explicit clears)
    self._explicit_fields: set[str] = set(data.keys())
    # Default "general" section to required=True, all others to required=False
    self.required: bool = data.get("required", data["key"] == "general")
    # Section dependencies - can be string or list of strings
    needs_value = data.get("needs")
    if needs_value:
      if isinstance(needs_value, str):
        self.needs: List[str] = [needs_value]
      elif isinstance(needs_value, list):
        self.needs: List[str] = needs_value
      else:
        raise ValueError(f"Section '{self.key}' has invalid 'needs' value: must be string or list")
    else:
      self.needs: List[str] = []

  def to_dict(self) -> Dict[str, Any]:
    """Serialize VariableSection to a dictionary for storage."""
    section_dict = {
      'required': self.required,
      'vars': {name: var.to_dict() for name, var in self.variables.items()}
    }
    
    # Add optional fields if present
    for field in ('title', 'description', 'toggle'):
      if value := getattr(self, field):
        section_dict[field] = value
    
    # Store dependencies (single value if only one, list otherwise)
    if self.needs:
      section_dict['needs'] = self.needs[0] if len(self.needs) == 1 else self.needs
    
    return section_dict
  
  def is_enabled(self) -> bool:
    """Check if section is currently enabled based on toggle variable.
    
    Returns:
        True if section is enabled (no toggle or toggle is True), False otherwise
    """
    if not self.toggle:
      return True
    
    toggle_var = self.variables.get(self.toggle)
    if not toggle_var:
      return True
    
    try:
      return bool(toggle_var.convert(toggle_var.value))
    except Exception:
      return False
  
  def clone(self, origin_update: Optional[str] = None) -> 'VariableSection':
    """Create a deep copy of the section with all variables.
    
    This is more efficient than converting to dict and back when copying sections.
    
    Args:
        origin_update: Optional origin string to apply to all cloned variables
        
    Returns:
        New VariableSection instance with deep-copied variables
        
    Example:
        section2 = section1.clone(origin_update='template')
    """
    # Create new section with same metadata
    cloned = VariableSection({
      'key': self.key,
      'title': self.title,
      'description': self.description,
      'toggle': self.toggle,
      'required': self.required,
      'needs': self.needs.copy() if self.needs else None,
    })
    
    # Deep copy all variables
    for var_name, variable in self.variables.items():
      if origin_update:
        cloned.variables[var_name] = variable.clone(update={'origin': origin_update})
      else:
        cloned.variables[var_name] = variable.clone()
    
    return cloned
