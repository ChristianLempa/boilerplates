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
  # SECTION: Validation Helpers
  # -------------------------

  def _validate_not_empty(self, value: Any, converted_value: Any) -> None:
    """Validate that a value is not empty for non-boolean types."""
    if self.type not in ["bool"] and (converted_value is None or converted_value == ""):
      raise ValueError("value cannot be empty")

  def _validate_enum_option(self, value: str) -> None:
    """Validate that a value is in the allowed enum options."""
    if self.options and value not in self.options:
      raise ValueError(f"value must be one of: {', '.join(self.options)}")

  def _validate_regex_pattern(self, value: str, pattern: re.Pattern, error_msg: str) -> None:
    """Validate that a value matches a regex pattern."""
    if not pattern.fullmatch(value):
      raise ValueError(error_msg)

  def _validate_url_structure(self, parsed_url) -> None:
    """Validate that a parsed URL has required components."""
    if not (parsed_url.scheme and parsed_url.netloc):
      raise ValueError("value must be a valid URL (include scheme and host)")

  # !SECTION

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
    self._validate_enum_option(val)
    return val

  def _convert_hostname(self, value: Any) -> str:
    """Convert and validate hostname."""
    val = str(value).strip()
    if not val:
      return ""
    if val.lower() != "localhost":
      self._validate_regex_pattern(val, HOSTNAME_REGEX, "value must be a valid hostname")
    return val

  def _convert_url(self, value: Any) -> str:
    """Convert and validate URL."""
    val = str(value).strip()
    if not val:
      return ""
    parsed = urlparse(val)
    self._validate_url_structure(parsed)
    return val

  def _convert_email(self, value: Any) -> str:
    """Convert and validate email."""
    val = str(value).strip()
    if not val:
      return ""
    self._validate_regex_pattern(val, EMAIL_REGEX, "value must be a valid email address")
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
    
    self._sections: Dict[str, VariableSection] = {}
    # NOTE: The _variable_map provides a flat, O(1) lookup for any variable by its name,
    # avoiding the need to iterate through sections. It stores references to the same
    # Variable objects contained in the _set structure.
    self._variable_map: Dict[str, Variable] = {}
    self._initialize_sections(spec)

  def _initialize_sections(self, spec: dict[str, Any]) -> None:
    """Initialize sections from the spec."""
    for section_key, section_data in spec.items():
      if not isinstance(section_data, dict):
        continue
      
      section = self._create_section(section_key, section_data)
      self._initialize_variables(section, section_data.get("vars", {}))
      self._sections[section_key] = section

  def _create_section(self, key: str, data: dict[str, Any]) -> VariableSection:
    """Create a VariableSection from data."""
    section_init_data = {
      "key": key,
      "title": data.get("title", key.replace("_", " ").title()),
      "prompt": data.get("prompt"),
      "description": data.get("description"),
      "toggle": data.get("toggle"),
      "required": data.get("required", key == "general")
    }
    return VariableSection(section_init_data)

  def _initialize_variables(self, section: VariableSection, vars_data: dict[str, Any]) -> None:
    """Initialize variables for a section."""
    for var_name, var_data in vars_data.items():
      var_init_data = {"name": var_name, **var_data}
      variable = Variable(var_init_data)
      section.variables[var_name] = variable
      # NOTE: Populate the direct lookup map for efficient access.
      self._variable_map[var_name] = variable

  # -------------------------
  # SECTION: Helper Methods
  # -------------------------

  # NOTE: These helper methods reduce code duplication across module.py and prompt.py
  # by centralizing common variable collection operations

  def get_all_values(self) -> dict[str, Any]:
    """Get all variable values as a dictionary."""
    # NOTE: This method is optimized to use the _variable_map for direct O(1) access
    # to each variable, which is much faster than iterating through sections.
    all_values = {}
    for var_name, variable in self._variable_map.items():
      all_values[var_name] = variable.get_typed_value()
    return all_values

  def apply_overrides(self, overrides: dict[str, Any], origin_suffix: str = " -> cli") -> list[str]:
    """Apply multiple variable overrides at once."""
    # NOTE: This method uses the _variable_map for a significant performance gain,
    # as it allows direct O(1) lookup of variables instead of iterating
    # through all sections to find a match.
    successful_overrides = []
    errors = []
    
    for var_name, value in overrides.items():
      try:
        variable = self._variable_map.get(var_name)
        if not variable:
          logger.warning(f"Variable '{var_name}' not found in template")
          continue
        
        # Convert and set the new value
        converted_value = variable.convert(value)
        variable.value = converted_value
        
        # Update origin to show override
        if variable.origin:
          variable.origin = variable.origin + origin_suffix
        else:
          variable.origin = origin_suffix.lstrip(" -> ")
        
        successful_overrides.append(var_name)
          
      except ValueError as e:
        error_msg = f"Invalid override value for '{var_name}': {value} - {e}"
        errors.append(error_msg)
        logger.error(error_msg)
    
    if errors:
      logger.warning(f"Some CLI overrides failed: {'; '.join(errors)}")
    
  def validate_all(self) -> None:
    """Validate all variables in the collection, skipping disabled sections."""
    for section in self._sections.values():
      # Check if the section is disabled by a toggle
      if section.toggle:
        toggle_var = section.variables.get(section.toggle)
        if toggle_var and not toggle_var.get_typed_value():
          logger.debug(f"Skipping validation for disabled section: '{section.key}'")
          continue  # Skip this entire section

      for var_name, variable in section.variables.items():
        try:
          variable.validate(variable.value)
        except ValueError as e:
          raise ValueError(f"Validation failed for variable '{var_name}': {e}") from e

  # !SECTION

# !SECTION
