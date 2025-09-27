from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse
import logging
import re

logger = logging.getLogger(__name__)

# -----------------------
# SECTION: Constants
# -----------------------

TRUE_VALUES = {"true", "1", "yes", "on"}
FALSE_VALUES = {"false", "0", "no", "off"}
HOSTNAME_REGEX = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9_-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9_-]{1,63}(?<!-))*$")
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# !SECTION

# ----------------------
# SECTION: Variable Class
# ----------------------

class Variable:
  """Represents a single templating variable with lightweight validation."""

  def __init__(self, data: dict[str, Any]) -> None:
    """Initialize Variable from a dictionary containing variable specification.
    
    Args:
        data: Dictionary containing variable specification with required 'name' key
              and optional keys: description, type, options, prompt, value, default, section, origin
              
    Raises:
        ValueError: If data is not a dict, missing 'name' key, or has invalid default value
    """
    # Validate input
    if not isinstance(data, dict):
      raise ValueError("Variable data must be a dictionary")
    
    if "name" not in data:
      raise ValueError("Variable data must contain 'name' key")
    
    # Initialize fields
    self.name: str = data["name"]
    self.description: Optional[str] = data.get("description") or data.get("display", "")
    self.type: str = data.get("type", "str")
    self.options: Optional[List[Any]] = data.get("options", [])
    self.prompt: Optional[str] = data.get("prompt")
    self.value: Any = data.get("value") if data.get("value") is not None else data.get("default")
    self.section: Optional[str] = data.get("section")
    self.origin: Optional[str] = data.get("origin")

    # Validate and convert the default/initial value if present
    if self.value is not None:
      try:
        self.value = self.convert(self.value)
      except ValueError as exc:
        raise ValueError(f"Invalid default for variable '{self.name}': {exc}")

  # -------------------------
  # SECTION: Type Conversion
  # -------------------------

  def convert(self, value: Any) -> Any:
    """Validate and convert a raw value based on the variable type."""
    if value is None:
      return None

    # Type conversion mapping for cleaner code
    converters = {
      "bool": self._convert_bool,
      "int": self._convert_int, 
      "float": self._convert_float,
      "enum": self._convert_enum,
      "hostname": self._convert_hostname,
      "url": self._convert_url,
      "email": self._convert_email,
    }
    
    converter = converters.get(self.type)
    if converter:
      return converter(value)
    
    # Default to string conversion
    return str(value)

  def _convert_bool(self, value: Any) -> bool:
    """Convert value to boolean."""
    if isinstance(value, bool):
      return value
    if isinstance(value, str):
      lowered = value.strip().lower()
      if lowered in TRUE_VALUES:
        return True
      if lowered in FALSE_VALUES:
        return False
    raise ValueError("value must be a boolean (true/false)")

  def _convert_int(self, value: Any) -> Optional[int]:
    """Convert value to integer."""
    if isinstance(value, int):
      return value
    if isinstance(value, str) and value.strip() == "":
      return None
    try:
      return int(value)
    except (TypeError, ValueError) as exc:
      raise ValueError("value must be an integer") from exc

  def _convert_float(self, value: Any) -> Optional[float]:
    """Convert value to float."""
    if isinstance(value, float):
      return value
    if isinstance(value, str) and value.strip() == "":
      return None
    try:
      return float(value)
    except (TypeError, ValueError) as exc:
      raise ValueError("value must be a float") from exc

  def _convert_enum(self, value: Any) -> Optional[str]:
    """Convert value to enum option."""
    if value == "":
      return None
    val = str(value)
    if self.options and val not in self.options:
      raise ValueError(f"value must be one of: {', '.join(self.options)}")
    return val

  def _convert_hostname(self, value: Any) -> str:
    """Convert and validate hostname."""
    val = str(value).strip()
    if not val:
      return ""
    if val.lower() == "localhost":
      return val
    if not HOSTNAME_REGEX.fullmatch(val):
      raise ValueError("value must be a valid hostname")
    return val

  def _convert_url(self, value: Any) -> str:
    """Convert and validate URL."""
    val = str(value).strip()
    if not val:
      return ""
    parsed = urlparse(val)
    if not (parsed.scheme and parsed.netloc):
      raise ValueError("value must be a valid URL (include scheme and host)")
    return val

  def _convert_email(self, value: Any) -> str:
    """Convert and validate email."""
    val = str(value).strip()
    if not val:
      return ""
    if not EMAIL_REGEX.fullmatch(val):
      raise ValueError("value must be a valid email address")
    return val

  def get_typed_value(self) -> Any:
    """Return the stored value converted to the appropriate Python type."""
    return self.convert(self.value)

  # !SECTION

# !SECTION

# ----------------------------
# SECTION: VariableSection Class
# ----------------------------

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
    self.prompt: Optional[str] = data.get("prompt")
    self.description: Optional[str] = data.get("description")
    self.toggle: Optional[str] = data.get("toggle")
    # Default "general" section to required=True, all others to required=False
    self.required: bool = data.get("required", data["key"] == "general")

  def variable_names(self) -> list[str]:
    return list(self.variables.keys())

# !SECTION

# --------------------------------
# SECTION: VariableCollection Class
# --------------------------------

class VariableCollection:
  """Manages variables grouped by sections and builds Jinja context."""

  def __init__(self, spec: dict[str, Any]) -> None:
    """Initialize VariableCollection from a specification dictionary.
    
    Args:
        spec: Dictionary containing the complete variable specification structure
              Expected format (as used in compose.py):
              {
                "section_key": {
                  "title": "Section Title",
                  "prompt": "Optional prompt text",
                  "toggle": "optional_toggle_var_name", 
                  "description": "Optional description",
                  "vars": {
                    "var_name": {
                      "description": "Variable description",
                      "type": "str",
                      "default": "default_value",
                      ...
                    }
                  }
                }
              }
    """
    if not isinstance(spec, dict):
      raise ValueError("Spec must be a dictionary")
    
    self._set: Dict[str, VariableSection] = {}
    
    # Initialize sections and their variables
    for section_key, section_data in spec.items():
      if not isinstance(section_data, dict):
        continue
        
      # Create section data with the key included
      section_init_data = {
        "key": section_key,
        "title": section_data.get("title", section_key.replace("_", " ").title()),
        "prompt": section_data.get("prompt"),
        "description": section_data.get("description"),
        "toggle": section_data.get("toggle"),
        "required": section_data.get("required", section_key == "general")
      }
      
      section = VariableSection(section_init_data)
      
      # Initialize variables in this section
      if "vars" in section_data:
        for var_name, var_data in section_data["vars"].items():
          # Add variable name to the data
          var_init_data = {"name": var_name, **var_data}
          variable = Variable(var_init_data)
          section.variables[var_name] = variable
      
      self._set[section_key] = section

  # -------------------------
  # SECTION: Helper Methods
  # -------------------------

  # NOTE: These helper methods reduce code duplication across module.py and prompt.py
  # by centralizing common variable collection operations

  def get_all_values(self) -> dict[str, Any]:
    """Get all variable values as a dictionary.
    Returns:
      Dictionary mapping variable names to their typed values
    """

    # NOTE: Eliminates the need to iterate through sections and variables manually
    # in module.py _extract_current_variable_values() method

    all_values = {}
    for section in self._set.values():
      for var_name, variable in section.variables.items():
        all_values[var_name] = variable.get_typed_value()
    return all_values

  def apply_overrides(self, overrides: dict[str, Any], origin_suffix: str = " -> cli") -> list[str]:
    """Apply multiple variable overrides at once.
    
    Args:
      overrides: Dictionary of variable names to values
      origin_suffix: Suffix to append to origins for overridden variables
      
    Returns:
      List of variable names that were successfully overridden
    """

    # NOTE: Replaces the complex _apply_cli_overrides() method in module.py
    # by centralizing override logic with proper error handling and origin tracking

    successful_overrides = []
    errors = []
    
    for var_name, value in overrides.items():
      try:
        # Find and update the variable
        found = False
        for section in self._set.values():
          if var_name in section.variables:
            variable = section.variables[var_name]
            
            # Convert and set the new value
            converted_value = variable.convert(value)
            variable.value = converted_value
            
            # Update origin to show override
            if variable.origin:
              variable.origin = variable.origin + origin_suffix
            else:
              variable.origin = origin_suffix.lstrip(" -> ")
            
            successful_overrides.append(var_name)
            found = True
            break
        
        if not found:
          logger.warning(f"Variable '{var_name}' not found in template")
          
      except ValueError as e:
        error_msg = f"Invalid override value for '{var_name}': {value} - {e}"
        errors.append(error_msg)
        logger.error(error_msg)
    
    if errors:
      # Log errors but don't stop the process
      logger.warning(f"Some CLI overrides failed: {'; '.join(errors)}")
    
    return successful_overrides

  # !SECTION

# !SECTION
