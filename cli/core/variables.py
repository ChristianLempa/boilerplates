from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


@dataclass
class Variable:
  """Represents a single templating variable.
  
  Supported types: str, int, float, bool, enum
  """
  name: str
  description: Optional[str] = None
  type: str = "str"  # str, int, float, bool, enum
  options: Optional[List[Any]] = field(default_factory=list)
  prompt: Optional[str] = None
  value: Any = None

  @classmethod
  def from_dict(cls, name: str, data: dict) -> "Variable":
    """Unified constructor for dict-based specs (module or frontmatter).
    Accepts keys: description/display, type, options, prompt, value/default.
    """
    return cls(
      name=name,
      description=data.get("description") or data.get("display", ""),
      type=data.get("type", "str"),
      options=data.get("options", []),
      prompt=data.get("prompt"),
      value=data.get("value") if data.get("value") is not None else data.get("default")
    )

  def get_typed_value(self) -> Any:
    """Return the value converted to the appropriate Python type."""
    if self.value is None:
      return None

    if self.type == "bool":
      if isinstance(self.value, bool):
        return self.value
      return str(self.value).lower() in ("true", "1", "yes", "on")
    if self.type == "int":
      return int(self.value)
    if self.type == "float":
      return float(self.value)
    return str(self.value)


@dataclass
class VariableCollection:
  """Manages variables with merge precedence and builds Jinja context.

  Flat model: context is a simple name -> typed value mapping.
  """

  variables: Dict[str, Variable] = field(default_factory=dict)

  def add_from_dict(self, specs: Dict[str, Any], used_vars: Set[str], label: str = "spec") -> None:
    """Generic adder that accepts a mapping of name -> (Variable | dict spec).

    - Preserves declaration order
    - Filters by used_vars
    - Uses Variable.from_dict for dict specs
    """
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
    """Apply Jinja2 defaults to variables that do not have a value yet."""
    for var_name, default_value in jinja_defaults.items():
      if var_name in self.variables:
        if self.variables[var_name].value is None or self.variables[var_name].value == "":
          self.variables[var_name].value = default_value
          logger.debug(f"Applied Jinja2 default to '{var_name}': {default_value}")

  def to_jinja_context(self) -> Dict[str, Any]:
    """Convert the collection to a flat dict suitable for Jinja rendering.

    Compatibility: for any '<section>_enabled' boolean, also expose '<section>' for
    legacy templates that expect a truthy/falsey root variable.
    """
    context: Dict[str, Any] = {}

    # First pass: direct mapping
    for var_name, variable in self.variables.items():
      value = variable.get_typed_value()
      if value is None:
        value = ""  # Avoid None in Jinja output
      context[var_name] = value

    # Second pass: alias *_enabled -> root
    for var_name, variable in self.variables.items():
      if var_name.endswith("_enabled"):
        root = var_name[: -len("_enabled")]
        context[root] = bool(variable.get_typed_value())

    return context

  def get_variable_names(self) -> List[str]:
    """Get variable names in insertion order."""
    return list(self.variables.keys())

  def get_variable(self, name: str) -> Optional[Variable]:
    """Get a specific variable by name."""
    return self.variables.get(name)

  def __len__(self) -> int:
    """Number of variables in the collection."""
    return len(self.variables)
