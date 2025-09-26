from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse
import logging
import re

logger = logging.getLogger(__name__)

TRUE_VALUES = {"true", "1", "yes", "on"}
FALSE_VALUES = {"false", "0", "no", "off"}
HOSTNAME_REGEX = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9_-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9_-]{1,63}(?<!-))*$")
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class Variable:
  """Represents a single templating variable with lightweight validation."""

  name: str
  description: Optional[str] = None
  type: str = "str"
  options: Optional[List[Any]] = field(default_factory=list)
  prompt: Optional[str] = None
  value: Any = None
  section: Optional[str] = None

  @classmethod
  def from_dict(cls, name: str, data: dict) -> "Variable":
    """Unified constructor for dict-based specs (module or frontmatter)."""
    variable = cls(
      name=name,
      description=data.get("description") or data.get("display", ""),
      type=data.get("type", "str"),
      options=data.get("options", []),
      prompt=data.get("prompt"),
      value=data.get("value") if data.get("value") is not None else data.get("default"),
      section=data.get("section"),
    )

    if variable.value is not None:
      try:
        variable.value = variable.convert(variable.value)
      except ValueError as exc:
        raise ValueError(f"Invalid default for variable '{name}': {exc}")

    return variable

  def convert(self, value: Any) -> Any:
    """Validate and convert a raw value based on the variable type."""
    if value is None:
      return None

    if self.type == "bool":
      if isinstance(value, bool):
        return value
      if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in TRUE_VALUES:
          return True
        if lowered in FALSE_VALUES:
          return False
      raise ValueError("value must be a boolean (true/false)")

    if self.type == "int":
      if isinstance(value, int):
        return value
      if isinstance(value, str) and value.strip() == "":
        return None
      try:
        return int(value)
      except (TypeError, ValueError) as exc:
        raise ValueError("value must be an integer") from exc

    if self.type == "float":
      if isinstance(value, float):
        return value
      if isinstance(value, str) and value.strip() == "":
        return None
      try:
        return float(value)
      except (TypeError, ValueError) as exc:
        raise ValueError("value must be a float") from exc

    if self.type == "enum":
      if value == "":
        return None
      val = str(value)
      if self.options and val not in self.options:
        raise ValueError(f"value must be one of: {', '.join(self.options)}")
      return val

    if self.type == "hostname":
      val = str(value).strip()
      if not val:
        return ""
      if val.lower() == "localhost":
        return val
      if not HOSTNAME_REGEX.fullmatch(val):
        raise ValueError("value must be a valid hostname")
      return val

    if self.type == "url":
      val = str(value).strip()
      if not val:
        return ""
      parsed = urlparse(val)
      if not (parsed.scheme and parsed.netloc):
        raise ValueError("value must be a valid URL (include scheme and host)")
      return val

    if self.type == "email":
      val = str(value).strip()
      if not val:
        return ""
      if not EMAIL_REGEX.fullmatch(val):
        raise ValueError("value must be a valid email address")
      return val

    # Default to string conversion, trimming trailing newline characters only
    return str(value)

  def get_typed_value(self) -> Any:
    """Return the stored value converted to the appropriate Python type."""
    return self.convert(self.value)


@dataclass
class VariableCollection:
  """Manages variables with merge precedence and builds Jinja context."""

  variables: Dict[str, Variable] = field(default_factory=dict)

  def add_from_dict(self, specs: Dict[str, Any], used_vars: Set[str], label: str = "spec") -> None:
    used = set(used_vars)
    for name in specs.keys():
      if name not in used:
        continue
      spec = specs[name]
      if isinstance(spec, Variable):
        self.variables[name] = spec
        logger.debug(f"Added {label} variable '{name}': {spec.description} (type: {spec.type})")
      elif isinstance(spec, dict):
        variable = Variable.from_dict(name, spec)
        self.variables[name] = variable
        logger.debug(f"Added {label} variable '{name}' (dict): {variable.description} (type: {variable.type})")
      else:
        logger.warning(
          f"Invalid {label} variable for '{name}': expected Variable or dict, got {type(spec).__name__}"
        )

  def apply_jinja_defaults(self, jinja_defaults: Dict[str, str]) -> None:
    for var_name, default_value in jinja_defaults.items():
      if var_name in self.variables:
        if self.variables[var_name].value is None or self.variables[var_name].value == "":
          try:
            self.variables[var_name].value = self.variables[var_name].convert(default_value)
            logger.debug(f"Applied Jinja2 default to '{var_name}': {default_value}")
          except ValueError as exc:
            logger.warning(f"Ignoring invalid Jinja default for '{var_name}': {exc}")

  def to_jinja_context(self) -> Dict[str, Any]:
    context: Dict[str, Any] = {}

    for var_name, variable in self.variables.items():
      try:
        value = variable.get_typed_value()
      except ValueError as exc:
        raise ValueError(f"Invalid value for variable '{var_name}': {exc}") from exc
      if value is None:
        value = ""
      context[var_name] = value

    for var_name, variable in self.variables.items():
      if var_name.endswith("_enabled"):
        root = var_name[: -len("_enabled")]
        context[root] = bool(variable.get_typed_value())

    return context

  def get_variable_names(self) -> List[str]:
    return list(self.variables.keys())

  def get_variable(self, name: str) -> Optional[Variable]:
    return self.variables.get(name)

  def as_rows(self) -> List[Dict[str, Any]]:
    """Return variable metadata for presentation or export."""
    rows: List[Dict[str, Any]] = []
    for name in self.get_variable_names():
      variable = self.variables[name]
      default = variable.get_typed_value()
      rows.append(
        {
          "name": name,
          "type": variable.type,
          "description": variable.description or "",
          "default": "" if default in (None, "") else str(default),
          "options": list(variable.options or []),
          "section": variable.section,
        }
      )
    return rows

  def __len__(self) -> int:
    return len(self.variables)
