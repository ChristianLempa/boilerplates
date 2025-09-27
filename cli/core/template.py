from __future__ import annotations

from .variables import Variable, VariableCollection
from pathlib import Path
from typing import Any, Dict, List, Set
from dataclasses import dataclass, field
import logging
from jinja2 import Environment, BaseLoader, meta, nodes
import frontmatter

logger = logging.getLogger(__name__)


# -----------------------
# SECTION: Metadata Class
# -----------------------

@dataclass
class TemplateMetadata:
  """Represents template metadata with proper typing."""
  name: str
  description: str
  author: str
  date: str
  version: str
  module: str = ""
  tags: List[str] = field(default_factory=list)
  files: List[str] = field(default_factory=list)
  library: str = "unknown"

  def __init__(self, post: frontmatter.Post, library_name: str | None = None) -> None:
    """Initialize TemplateMetadata from frontmatter post."""
    # Validate metadata format first
    self._validate_metadata(post)
    
    # Extract metadata section
    metadata_section = post.metadata.get("metadata", {})
    
    self.name = metadata_section.get("name", "")
    self.description = metadata_section.get("description", "No description available")
    self.author = metadata_section.get("author", "")
    self.date = metadata_section.get("date", "")
    self.version = metadata_section.get("version", "")
    self.module = metadata_section.get("module", "")
    self.tags = metadata_section.get("tags", []) or []
    self.files = metadata_section.get("files", []) or []
    self.library = library_name or "unknown"

  @staticmethod
  def _validate_metadata(post: frontmatter.Post) -> None:
    """Validate that template has required 'metadata' section with all required fields."""
    metadata_section = post.metadata.get("metadata")
    if metadata_section is None:
      raise ValueError("Template format error: missing 'metadata' section")
    
    # Validate that metadata section has all required fields
    required_fields = ["name", "author", "version", "date", "description"]
    missing_fields = [field for field in required_fields if not metadata_section.get(field)]
    
    if missing_fields:
      raise ValueError(f"Template format error: missing required metadata fields: {missing_fields}")

# !SECTION

# -----------------------
# SECTION: Template Class
# -----------------------

@dataclass
class Template:
  """Represents a template file with frontmatter and content."""

  def __init__(self, file_path: Path, library_name: str) -> None:
    """Create a Template instance from a file path."""
    logger.debug(f"Loading template from file: {file_path}")

    try:
      # Parse frontmatter and content from the file
      logger.debug(f"Loading template from file: {file_path}")
      with open(file_path, "r", encoding="utf-8") as f:
        post = frontmatter.load(f)

      # Load metadata using the TemplateMetadata constructor
      self.metadata = TemplateMetadata(post, library_name)
      logger.debug(f"Loaded metadata: {self.metadata}")

      # Validate 'kind' field presence
      self._validate_kind(post)

      # Load module specifications
      kind = post.metadata.get("kind", None)
      module_specs = {}
      if kind:
        try:
          import importlib
          module = importlib.import_module(f"..modules.{kind}", package=__package__)
          module_specs = getattr(module, 'spec', {})
        except Exception as e:
          raise ValueError(f"Error loading module specifications for kind '{kind}': {str(e)}")
      
      # Loading template variable specs - merge template specs with module specs
      template_specs = post.metadata.get("spec", {})
      
      # Deep merge specs: merge vars within sections instead of replacing entire sections
      # Preserve order: start with module spec order, then append template-only sections
      merged_specs = {}
      
      # First, process all sections from module spec (preserves order)
      for section_key in module_specs.keys():
        module_section = module_specs.get(section_key, {})
        template_section = template_specs.get(section_key, {})
        
        # Start with module section as base
        merged_section = {**module_section}
        
        # Merge template section metadata (title, prompt, etc.)
        for key in ['title', 'prompt', 'description', 'toggle', 'required']:
          if key in template_section:
            merged_section[key] = template_section[key]
        
        # Merge vars: template vars extend/override module vars
        module_vars = module_section.get('vars', {})
        template_vars = template_section.get('vars', {})
        merged_section['vars'] = {**module_vars, **template_vars}
        
        merged_specs[section_key] = merged_section
      
      # Then, add any sections that exist only in template spec
      for section_key in template_specs.keys():
        if section_key not in module_specs:
          template_section = template_specs[section_key]
          merged_section = {**template_section}
          merged_specs[section_key] = merged_section
      
      logger.debug(f"Loaded specs: {merged_specs}")

      self.file_path = file_path
      self.id = file_path.parent.name

      self.content = post.content
      logger.debug(f"Loaded content: {self.content}")

      # Extract variables used in template and their defaults
      self.jinja_env = self._create_jinja_env()
      ast = self.jinja_env.parse(self.content)
      used_variables: Set[str] = meta.find_undeclared_variables(ast)
      default_values: Dict[str, str] = self._extract_jinja_defaults(ast)
      logger.debug(f"Used variables: {used_variables}, defaults: {default_values}")

      # Validate that all used variables are defined in specs
      self._validate_variable_definitions(used_variables, merged_specs)

      # Filter specs to only used variables and merge in Jinja defaults
      filtered_specs = {}
      for section_key, section_data in merged_specs.items():
        if "vars" in section_data:
          filtered_vars = {}
          for var_name, var_data in section_data["vars"].items():
            if var_name in used_variables:
              # Determine origin: check where this variable comes from
              module_has_var = (section_key in module_specs and 
                               var_name in module_specs.get(section_key, {}).get("vars", {}))
              template_has_var = (section_key in template_specs and 
                                 var_name in template_specs.get(section_key, {}).get("vars", {}))
              
              if module_has_var and template_has_var:
                origin = "module -> template"  # Template overrides module
              elif template_has_var and not module_has_var:
                origin = "template"  # Template-only variable
              else:
                origin = "module"  # Module-only variable
              
              # Merge in Jinja default and origin if present
              var_data_with_origin = {**var_data, "origin": origin}
              if var_name in default_values:
                var_data_with_origin["default"] = default_values[var_name]
              elif "default" not in var_data_with_origin:
                var_data_with_origin["default"] = ""
                logger.warning(f"No default specified for variable '{var_name}' in template '{self.id}'")
              
              filtered_vars[var_name] = var_data_with_origin
          
          if filtered_vars:  # Only include sections that have used variables
            filtered_specs[section_key] = {**section_data, "vars": filtered_vars}

      # Create VariableCollection from filtered specs
      self.variables = VariableCollection(filtered_specs)

      logger.info(f"Loaded template '{self.id}' (v{self.metadata.version})")

    except ValueError as e:
      # FIXME: Refactor error handling to avoid redundant catching and re-raising
      # ValueError already logged in validation method - don't duplicate
      raise
    except FileNotFoundError:
      logger.error(f"Template file not found: {file_path}")
      raise
    except Exception as e:
      logger.error(f"Error loading template from {file_path}: {str(e)}")
      raise

  # ---------------------------
  # SECTION: Validation Methods
  # ---------------------------

  @staticmethod
  def _extract_jinja_defaults(ast: nodes.Node) -> dict[str, str]:
    """Extract default values from Jinja2 template variables with default filters."""
    defaults = {}
    
    def visit_node(node):
      """Recursively visit AST nodes to find default filter usage."""
      if isinstance(node, nodes.Filter):
        # Check if this is a 'default' filter
        if node.name == 'default' and len(node.args) > 0:
          # Get the variable being filtered
          if isinstance(node.node, nodes.Name):
            var_name = node.node.name
            # Get the default value (first argument to default filter)
            default_arg = node.args[0]
            if isinstance(default_arg, nodes.Const):
              defaults[var_name] = str(default_arg.value)
            elif isinstance(default_arg, nodes.Name):
              defaults[var_name] = default_arg.name
      
      # Recursively visit child nodes
      for child in node.iter_child_nodes():
        visit_node(child)
    
    visit_node(ast)
    return defaults

  @staticmethod
  def _validate_kind(post: frontmatter.Post) -> None:
    """Validate that template has required 'kind' field."""
    if not post.metadata.get("kind"):
      raise ValueError("Template format error: missing 'kind' field")

  def _validate_variable_definitions(self, used_variables: set[str], merged_specs: dict[str, Any]) -> None:
    """Validate that all variables used in Jinja2 content are defined in the spec.
    
    Args:
      used_variables: Set of variable names found in the Jinja2 template content
      merged_specs: Combined module and template specifications
      
    Raises:
      ValueError: If any used variables are not defined in the spec
    """
    # Collect all defined variables from all sections
    defined_variables = set()
    for section_data in merged_specs.values():
      if "vars" in section_data and isinstance(section_data["vars"], dict):
        defined_variables.update(section_data["vars"].keys())
    
    # Find variables used in template but not defined in spec
    undefined_variables = used_variables - defined_variables
    
    if undefined_variables:
      # Sort for consistent error messages
      undefined_list = sorted(undefined_variables)
      
      # Create detailed error message
      error_msg = (
        f"Template validation error in '{self.id}': "
        f"Variables used in template content but not defined in spec: {undefined_list}\n\n"
        f"Please add these variables to your template spec or module spec. "
        f"Example:\n"
        f"spec:\n"
        f"  general:\n"
        f"    vars:\n"
      )
      
      # Add example spec entries for each undefined variable
      for var_name in undefined_list:
        error_msg += (
          f"      {var_name}:\n"
          f"        type: str\n"
          f"        description: Description for {var_name}\n"
          f"        default: \"\"\n"
        )
      
      logger.error(error_msg)
      raise ValueError(error_msg)

  # !SECTION

  # ---------------------------------
  # SECTION: Jinja2 Rendering Methods
  # ---------------------------------

  @staticmethod
  def _create_jinja_env() -> Environment:
    """Create standardized Jinja2 environment for consistent template processing."""
    return Environment(
      loader=BaseLoader(),
      trim_blocks=True,
      lstrip_blocks=True,
      keep_trailing_newline=False,
    )

  def render(self, variables: dict[str, Any]) -> str:
    """Render the template with the given variables."""
    logger.debug(f"Rendering template '{self.id}' with variables: {variables}")
    template = self.jinja_env.from_string(self.content)
    return template.render(**variables)
  
  # !SECTION
