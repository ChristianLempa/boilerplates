from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class TemplateVariable:
  """Variable detected from template analysis.
  
  Represents a variable found in a template with all its properties:
  - Simple variables: service_name, container_name
  - Dotted variables: traefik.host, network.name, service_port.http
  - Enabler variables: Variables used in {% if var %} conditions
  """
  name: str
  default: Any = None
  type: str = "string"  # string, integer, float, boolean (inferred from default or usage)
  
  # Variable characteristics
  is_enabler: bool = False  # Used in {% if %} conditions
  
  # Grouping info (extracted from dotted notation)
  group: Optional[str] = None  # e.g., 'traefik' for 'traefik.host'
  
  @property
  def display_name(self) -> str:
    """Get display name for prompts."""
    if self.group:
      # Remove group prefix for display
      return self.name.replace(f"{self.group}.", "").replace(".", " ")
    return self.name.replace(".", " ")
  
  @property 
  def is_required(self) -> bool:
    """Check if variable is required (no default value)."""
    return self.default is None


def analyze_template_variables(
  vars_used: Set[str],
  var_defaults: Dict[str, Any],
  template_content: str
) -> Dict[str, TemplateVariable]:
  """Analyze template variables and create TemplateVariable objects.
  
  Args:
    vars_used: Set of all variable names used in template
    var_defaults: Dict of variable defaults from template
    template_content: The raw template content for additional analysis
  
  Returns:
    Dict mapping variable name to TemplateVariable object
  """
  variables = {}
  
  # Detect enabler variables (used in {% if %} conditions)
  enablers = _detect_enablers(template_content)
  
  for var_name in vars_used:
    var = TemplateVariable(
      name=var_name,
      default=var_defaults.get(var_name)
    )
    
    # Detect if it's an enabler
    var.is_enabler = var_name in enablers
    
    # Infer type from default value
    if var.default is not None:
      if isinstance(var.default, bool):
        var.type = "boolean"
      elif isinstance(var.default, int):
        var.type = "integer"
      elif isinstance(var.default, float):
        var.type = "float"
      else:
        var.type = "string"
    
    # If it's an enabler without a default, assume boolean
    if var.is_enabler and var.default is None:
      var.type = "boolean"
      var.default = False  # Default enablers to False
    
    # Detect group from dotted notation
    if '.' in var_name:
      var.group = var_name.split('.')[0]
    
    variables[var_name] = var
  
  return variables


def _detect_enablers(template_content: str) -> Set[str]:
  """Detect variables used as enablers in {% if %} conditions.
  
  Args:
    template_content: The raw template content
  
  Returns:
    Set of variable names that are used as enablers
  """
  import re
  enablers = set()
  
  # Find variables used in {% if var %} patterns
  # This catches: {% if var %}, {% if not var %}, {% if var and ... %}
  if_pattern = re.compile(r'{%\s*if\s+(not\s+)?(\w+)(?:\s|%)', re.MULTILINE)
  for match in if_pattern.finditer(template_content):
    var_name = match.group(2)
    # Skip Jinja2 keywords
    if var_name not in ['true', 'false', 'none', 'True', 'False', 'None']:
      enablers.add(var_name)
  
  return enablers
