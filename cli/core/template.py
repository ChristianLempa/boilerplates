from .variables import Variable, VariableCollection
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
import logging
import re
from jinja2 import Environment, BaseLoader, meta, nodes, TemplateSyntaxError
import frontmatter

logger = logging.getLogger(__name__)


@dataclass
class Template:
  """Represents a template file with frontmatter and content."""

  # Required fields
  file_path: Path
  content: str = ""

  # Frontmatter metadata
  id: str = ""
  name: str = ""
  description: str = "No description available"
  author: str = ""
  date: str = ""
  version: str = ""
  module: str = ""
  tags: List[str] = field(default_factory=list)
  files: List[str] = field(default_factory=list)

  # Extracted/merged variables
  variables: VariableCollection = field(default_factory=VariableCollection, init=False)
  # Source tracking for prompting and ordering
  template_var_names: List[str] = field(default_factory=list, init=False)
  module_var_names: List[str] = field(default_factory=list, init=False)

  def render(self, variable_values: Optional[Dict[str, Any]] = None) -> str:
    """Render the template with given variable overrides."""
    if variable_values:
      for name, value in variable_values.items():
        var = self.variables.get_variable(name)
        if var:
          var.value = value

    env = self._create_jinja_env()
    context = self.variables.to_jinja_context()
    template = env.from_string(self.content)
    return template.render(context)

  def get_variable_names(self) -> List[str]:
    """List variable names in insertion order."""
    return self.variables.get_variable_names()

  @classmethod
  def from_file(cls, file_path: Path, module_variables: Dict[str, Any] = None) -> "Template":
    """Create a Template instance from a file path."""
    logger.debug(f"Loading template from file: {file_path}")

    try:
      frontmatter_data, content = cls._parse_frontmatter(file_path)
      template_id = file_path.parent.name

      template = cls(
        file_path=file_path,
        content=content,
        id=template_id,
        name=frontmatter_data.get("name", ""),
        description=frontmatter_data.get("description", "No description available"),
        author=frontmatter_data.get("author", ""),
        date=frontmatter_data.get("date", ""),
        version=frontmatter_data.get("version", ""),
        module=frontmatter_data.get("module", ""),
        tags=frontmatter_data.get("tags", []),
        files=frontmatter_data.get("files", []),
      )

      logger.info(f"Loaded template '{template.id}' (v{template.version or 'unversioned'})")

      # Extract and merge variables (only those actually used)
      variables, tpl_names, mod_names = cls._merge_variables(content, frontmatter_data, module_variables or {})
      template.variables = variables
      template.template_var_names = tpl_names
      template.module_var_names = mod_names

      logger.debug(
        f"Final variables for template '{template.id}': {template.variables.get_variable_names()}"
      )

      return template

    except FileNotFoundError:
      logger.error(f"Template file not found: {file_path}")
      raise
    except Exception as e:
      logger.error(f"Error loading template from {file_path}: {str(e)}")
      raise

  @staticmethod
  def _create_jinja_env() -> Environment:
    """Create standardized Jinja2 environment for consistent template processing."""
    return Environment(
      loader=BaseLoader(),
      trim_blocks=True,
      lstrip_blocks=True,
      keep_trailing_newline=False,
    )

  @staticmethod
  def _parse_frontmatter(file_path: Path) -> Tuple[Dict[str, Any], str]:
    """Parse frontmatter and content from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
      post = frontmatter.load(f)
    return post.metadata, post.content

  @staticmethod
  def _extract_variables_from_frontmatter(frontmatter_data: Dict[str, Any]) -> Dict[str, Variable]:
    """Extract variables from the 'variables:' section in frontmatter as Variable objects.

    Example:
      variables:
        var_name:
          description: "..."
          type: "str"
    """
    variables_data = frontmatter_data.get("variables")
    result: Dict[str, Variable] = {}

    if not variables_data:
      return result

    try:
      if isinstance(variables_data, dict):
        for name, var_config in variables_data.items():
          if isinstance(var_config, dict):
            variable = Variable.from_dict(name, var_config)
            result[name] = variable
          else:
            logger.warning(
              f"Invalid variable configuration for '{name}': expected dict, got {type(var_config).__name__}"
            )
      else:
        raise ValueError(
          "Variables must be a dictionary. Use format: variables: { var_name: { type: 'str' } }"
        )
    except Exception as e:
      logger.error(f"Error parsing variables from frontmatter: {str(e)}")
      return {}

    logger.debug(
      f"Extracted {len(result)} variables (insertion order preserved): {list(result.keys())}"
    )
    return result

  @staticmethod
  def _extract_template_variables(content: str) -> Set[str]:
    """Extract variable names used in Jinja2 template content (flat names only).

    Strategy:
    - Use Jinja2 AST to find undeclared variables
    - Ignore dotted and bracket access (templates should use flat names only)
    """
    try:
      env = Template._create_jinja_env()
      ast = env.parse(content)
      root_variables = meta.find_undeclared_variables(ast)
      logger.debug(f"Found variables: {sorted(root_variables)}")
      return set(root_variables)
    except TemplateSyntaxError as e:
      logger.warning(f"Template syntax error while analyzing variables: {e}")
      return set()
    except Exception as e:
      logger.warning(f"Error analyzing template variables: {e}")
      return set()

  @staticmethod
  def _extract_jinja_defaults(content: str) -> Dict[str, str]:
    """Extract default values from Jinja2 | default() filters for flat names."""
    defaults: Dict[str, str] = {}
    try:
      # Flat var names only (no dots). Single or double quotes supported
      default_pattern = r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\|\s*default\(\s*['\"]([^'\"]*)['\"]\s*\)"
      matches = re.findall(default_pattern, content)
      for var_name, default_value in matches:
        defaults[var_name.strip()] = default_value
      logger.debug(f"Found Jinja2 defaults: {defaults}")
      return defaults
    except Exception as e:
      logger.warning(f"Error extracting Jinja2 defaults: {e}")
      return {}

  @staticmethod
  def _merge_variables(
    content: str,
    frontmatter_data: Dict[str, Any],
    module_variables: Dict[str, Any],
  ) -> Tuple[VariableCollection, List[str], List[str]]:
    """Merge module + frontmatter vars, auto-create missing, and apply Jinja defaults.

    Precedence (highest to lowest when a value exists):
      1. Template frontmatter variables
      2. Jinja | default() values (only if no value is set)
      3. Module variables
      4. Auto-created variables for what's used in content
    """
    used_variables = Template._extract_template_variables(content)
    jinja_defaults = Template._extract_jinja_defaults(content)

    if not used_variables:
      logger.debug("No variables found in template content")
      return VariableCollection()

    variables = VariableCollection()

    logger.debug(
      f"Processing module variables: {list(module_variables.keys()) if module_variables else []}"
    )

    # Compatibility bridge: if module defines *_enabled toggles and legacy roots are used
    # (e.g., 'traefik' in template), ensure '<root>_enabled' is also included and map defaults.
    toggle_roots = {k[:-len('_enabled')] for k in module_variables.keys() if k.endswith('_enabled')}

    # Add missing toggles for used legacy roots
    bridged_used = set(used_variables)
    for root in toggle_roots:
      if root in used_variables:
        bridged_used.add(f"{root}_enabled")

    # Map Jinja defaults from legacy roots to *_enabled toggles
    bridged_defaults = dict(jinja_defaults)
    for root in toggle_roots:
      if root in jinja_defaults and f"{root}_enabled" not in bridged_defaults:
        bridged_defaults[f"{root}_enabled"] = jinja_defaults[root]

    # 1) Module variables (lowest precedence)
    variables.add_from_dict(module_variables, bridged_used, label="module")

    # 2) Frontmatter variables (override module specs)
    template_vars = Template._extract_variables_from_frontmatter(frontmatter_data)
    variables.add_from_dict(template_vars, bridged_used, label="template")

    # Track source ordering lists
    template_var_names_ordered: List[str] = [n for n in template_vars.keys() if n in bridged_used]
    module_var_names_ordered: List[str] = [n for n in module_variables.keys() if n in bridged_used]

    # 3) Auto-create missing variables for anything used in the template
    defined_names = set(variables.variables.keys())
    missing = bridged_used - defined_names

    # Auto-create missing variables (flat names only). Skip legacy roots if their *_enabled exists.
    for name in sorted(missing):
      if name in toggle_roots:
        # Will be provided via alias from '<root>_enabled'
        logger.debug(f"Skipping auto-create for legacy root '{name}' (alias provided by *_enabled)")
        continue
      variables.variables[name] = Variable(name=name, type="str")
      logger.debug(f"Auto-created variable '{name}' (flat)")

    # Apply Jinja defaults last (only fill if still empty)
    variables.apply_jinja_defaults(bridged_defaults)

    logger.debug(
      f"Smart merge: {len(bridged_used)} used, {len(variables)} defined = {len(variables)} final variables"
    )
    return variables, template_var_names_ordered, module_var_names_ordered
