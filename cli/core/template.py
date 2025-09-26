from .variables import Variable, VariableCollection
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import OrderedDict
import logging
import re
from jinja2 import Environment, BaseLoader, meta, nodes, TemplateSyntaxError
import frontmatter

logger = logging.getLogger(__name__)


def _log_variable_stage(stage: str, names) -> None:
  """Helper to emit consistent debug output for variable lists."""
  if not names:
    return
  if isinstance(names, (set, tuple)):
    names = list(names)
  logger.debug(f"{stage}: {names}")


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
  library: str = ""
  variable_sections: "OrderedDict[str, Dict[str, Any]]" = field(default_factory=OrderedDict, init=False)

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
          try:
            var.value = var.convert(value)
          except ValueError as exc:
            raise ValueError(f"Invalid value for variable '{name}': {exc}")

    env = self._create_jinja_env()
    context = self.variables.to_jinja_context()
    template = env.from_string(self.content)
    return template.render(context)

  def get_variable_names(self) -> List[str]:
    """List variable names in insertion order."""
    return self.variables.get_variable_names()

  @classmethod
  def from_file(
    cls,
    file_path: Path,
    module_sections: Dict[str, Any] = None,
    library_name: str = ""
  ) -> "Template":
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
        library=library_name,
      )

      logger.info(f"Loaded template '{template.id}' (v{template.version or 'unversioned'})")

      module_section_defs = module_sections or {}
      module_flat, module_section_meta = cls._flatten_sections(module_section_defs)

      template_section_defs = frontmatter_data.get("variable_sections") or {}
      legacy_frontmatter_vars = frontmatter_data.get("variables")
      if legacy_frontmatter_vars:
        template_section_defs = OrderedDict(template_section_defs)
        template_section_defs["template_specific"] = {
          "title": f"{template.name or template_id} Specific",
          "prefix": "",
          "vars": legacy_frontmatter_vars,
        }

      template_flat, template_section_meta = cls._flatten_sections(template_section_defs)

      # Extract and merge variables (only those actually used)
      variables, tpl_names, mod_names = cls._merge_variables(
        content,
        module_flat,
        template_flat,
        template_id,
      )
      template.variables = variables
      template.template_var_names = tpl_names
      template.module_var_names = mod_names
      template.variable_sections = cls._combine_sections_meta(
        module_section_meta,
        template_section_meta,
        template.variables,
      )

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
    module_variables: Dict[str, Any],
    template_variables: Dict[str, Any],
    template_id: str,
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

    declared_variables = set(module_variables.keys()) | set(template_variables.keys())
    missing_declared = used_variables - declared_variables
    if missing_declared:
      raise ValueError(
        "Unknown variables referenced in template: "
        + ", ".join(sorted(missing_declared))
      )

    variables = VariableCollection()

    # Keep only variables that are actually referenced in the template content,
    # plus any explicitly defined in template frontmatter.
    relevant_names = used_variables | set(template_variables.keys())

    _log_variable_stage(
      "Processing module variables",
      list(module_variables.keys()) if module_variables else [],
    )

    variables.add_from_dict(module_variables, relevant_names, label="module")
    variables.add_from_dict(template_variables, relevant_names, label="template")

    template_var_names_ordered: List[str] = [n for n in template_variables.keys() if n in relevant_names]
    module_var_names_ordered: List[str] = [n for n in module_variables.keys() if n in relevant_names]

    variables.apply_jinja_defaults(jinja_defaults)

    Template._ensure_defaults(variables, template_id)

    logger.debug(
      f"Smart merge: {len(relevant_names)} used, {len(variables)} defined = {len(variables)} final variables"
    )
    return variables, template_var_names_ordered, module_var_names_ordered

  @staticmethod
  def _ensure_defaults(variables: VariableCollection, template_id: str) -> None:
    """Ensure every variable has a default value; raise if any are missing."""
    missing: List[str] = []

    for var_name in variables.get_variable_names():
      variable = variables.get_variable(var_name)
      if not variable:
        continue
      if variable.value not in (None, ""):
        continue

      missing.append(var_name)

    if missing:
      raise ValueError(
        f"Missing default value(s) for variables {', '.join(missing)} in template '{template_id}'"
      )

  @staticmethod
  def _flatten_sections(
    section_defs: Dict[str, Any],
  ) -> Tuple[Dict[str, Dict[str, Any]], "OrderedDict[str, Dict[str, Any]]"]:
    flat: Dict[str, Dict[str, Any]] = {}
    meta: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()

    if not section_defs:
      return flat, meta

    for key, data in section_defs.items():
      if not isinstance(data, dict):
        continue

      title = data.get("title") or key.replace('_', ' ').title()
      toggle_name = data.get("toggle")
      vars_spec = data.get("vars") or {}

      variables_list: List[str] = []
      for var_name, spec in vars_spec.items():
        spec = dict(spec)
        spec.setdefault("section", title)
        flat[var_name] = spec
        variables_list.append(var_name)

      if toggle_name:
        if toggle_name not in flat:
          flat[toggle_name] = {
            "type": "bool",
            "default": False,
            "section": title,
            "description": data.get("toggle_description", ""),
          }
        if toggle_name not in variables_list:
          variables_list.insert(0, toggle_name)

      meta[key] = {
        "title": title,
        "prompt": data.get("prompt"),
        "description": data.get("description"),
        "toggle": toggle_name,
        "variables": variables_list,
      }

    return flat, meta

  @staticmethod
  def _combine_sections_meta(
    module_meta: "OrderedDict[str, Dict[str, Any]]",
    template_meta: "OrderedDict[str, Dict[str, Any]]",
    variables: VariableCollection,
  ) -> "OrderedDict[str, Dict[str, Any]]":
    combined: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()

    def _add_meta(source: "OrderedDict[str, Dict[str, Any]]") -> None:
      for key, meta in source.items():
        existing = combined.get(key)
        if existing:
          existing["variables"].extend(v for v in meta["variables"] if v not in existing["variables"])
          if meta.get("prompt"):
            existing["prompt"] = meta["prompt"]
          if meta.get("description"):
            existing["description"] = meta["description"]
          if meta.get("toggle"):
            existing["toggle"] = meta["toggle"]
          if meta.get("title"):
            existing["title"] = meta["title"]
        else:
          combined[key] = {
            "title": meta.get("title") or key.replace('_', ' ').title(),
            "prompt": meta.get("prompt"),
            "description": meta.get("description"),
            "toggle": meta.get("toggle"),
            "variables": list(meta.get("variables", [])),
          }

    _add_meta(module_meta)
    _add_meta(template_meta)

    # Filter out variables that are not present in the final collection
    existing_names = set(variables.get_variable_names())
    seen: Set[str] = set()
    for key, meta in list(combined.items()):
      filtered = [name for name in meta["variables"] if name in existing_names]
      if not filtered:
        del combined[key]
        continue
      meta["variables"] = filtered
      seen.update(filtered)

    # Add remaining variables that were not covered by sections
    remaining = [name for name in existing_names if name not in seen]
    if remaining:
      combined["other"] = {
        "title": "Other",
        "prompt": None,
        "description": None,
        "toggle": None,
        "variables": remaining,
      }

    return combined
