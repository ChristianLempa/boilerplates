from __future__ import annotations

from .variables import Variable, VariableCollection
from pathlib import Path
from typing import Any, Dict, List, Set, Optional, Literal
from dataclasses import dataclass, field
import logging
import os
import yaml
from jinja2 import Environment, FileSystemLoader, meta
from jinja2 import nodes
from jinja2.visitor import NodeVisitor

logger = logging.getLogger(__name__)


# -----------------------
# SECTION: TemplateFile Class
# -----------------------

@dataclass
class TemplateFile:
    """Represents a single file within a template directory."""
    relative_path: Path
    file_type: Literal['j2', 'static']
    output_path: Path # The path it will have in the output directory

# !SECTION

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
  # files: List[str] = field(default_factory=list) # No longer needed, as TemplateFile handles this
  library: str = "unknown"

  def __init__(self, template_data: dict, library_name: str | None = None) -> None:
    """Initialize TemplateMetadata from parsed YAML template data.
    
    Args:
        template_data: Parsed YAML data from template.yaml
        library_name: Name of the library this template belongs to
    """
    # Validate metadata format first
    self._validate_metadata(template_data)
    
    # Extract metadata section
    metadata_section = template_data.get("metadata", {})
    
    self.name = metadata_section.get("name", "")
    # YAML block scalar (|) preserves a trailing newline. Remove only trailing newlines
    # while preserving internal newlines/formatting.
    raw_description = metadata_section.get("description", "")
    if isinstance(raw_description, str):
      description = raw_description.rstrip("\n")
    else:
      description = str(raw_description)
    self.description = description or "No description available"
    self.author = metadata_section.get("author", "")
    self.date = metadata_section.get("date", "")
    self.version = metadata_section.get("version", "")
    self.module = metadata_section.get("module", "")
    self.tags = metadata_section.get("tags", []) or []
    # self.files = metadata_section.get("files", []) or [] # No longer needed
    self.library = library_name or "unknown"

  @staticmethod
  def _validate_metadata(template_data: dict) -> None:
    """Validate that template has required 'metadata' section with all required fields.
    
    Args:
        template_data: Parsed YAML data from template.yaml
        
    Raises:
        ValueError: If metadata section is missing or incomplete
    """
    metadata_section = template_data.get("metadata")
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
  """Represents a template directory."""

  def __init__(self, template_dir: Path, library_name: str) -> None:
    """Create a Template instance from a directory path."""
    logger.debug(f"Loading template from directory: {template_dir}")
    self.template_dir = template_dir
    self.id = template_dir.name
    self.library_name = library_name

    # Initialize caches for lazy loading
    self.__module_specs: Optional[dict] = None
    self.__merged_specs: Optional[dict] = None
    self.__jinja_env: Optional[Environment] = None
    self.__used_variables: Optional[Set[str]] = None
    self.__variables: Optional[VariableCollection] = None
    self.__template_files: Optional[List[TemplateFile]] = None # New attribute

    try:
      # Find and parse the main template file (template.yaml or template.yml)
      main_template_path = self._find_main_template_file()
      with open(main_template_path, "r", encoding="utf-8") as f:
        # Load all YAML documents (handles templates with empty lines before ---)
        documents = list(yaml.safe_load_all(f))
        
        # Filter out None/empty documents and get the first non-empty one
        valid_docs = [doc for doc in documents if doc is not None]
        
        if not valid_docs:
          raise ValueError("Template file contains no valid YAML data")
        
        if len(valid_docs) > 1:
          logger.warning(f"Template file contains multiple YAML documents, using the first one")
        
        self._template_data = valid_docs[0]
      
      # Validate template data
      if not isinstance(self._template_data, dict):
        raise ValueError("Template file must contain a valid YAML dictionary")

      # Load metadata (always needed)
      self.metadata = TemplateMetadata(self._template_data, library_name)
      logger.debug(f"Loaded metadata: {self.metadata}")

      # Validate 'kind' field (always needed)
      self._validate_kind(self._template_data)

      # Collect file paths (relatively lightweight, needed for various lazy loads)
      # This will now populate self.template_files
      self._collect_template_files()

      logger.info(f"Loaded template '{self.id}' (v{self.metadata.version})")

    except (ValueError, FileNotFoundError) as e:
      logger.error(f"Error loading template from {template_dir}: {e}")
      raise
    except Exception as e:
      logger.error(f"An unexpected error occurred while loading template {template_dir}: {e}")
      raise

  def _find_main_template_file(self) -> Path:
    """Find the main template file (template.yaml or template.yml)."""
    for filename in ["template.yaml", "template.yml"]:
      path = self.template_dir / filename
      if path.exists():
        return path
    raise FileNotFoundError(f"Main template file (template.yaml or template.yml) not found in {self.template_dir}")

  def _load_module_specs(self, kind: str) -> dict:
    """Load specifications from the corresponding module."""
    if not kind:
      return {}
    try:
      import importlib
      module = importlib.import_module(f"..modules.{kind}", package=__package__)
      return getattr(module, 'spec', {})
    except Exception as e:
      raise ValueError(f"Error loading module specifications for kind '{kind}': {e}")

  def _merge_specs(self, module_specs: dict, template_specs: dict) -> dict:
    """Deep merge template specs with module specs using VariableCollection.
    
    Uses VariableCollection's native merge() method for consistent merging logic.
    Module specs are base, template specs override with origin tracking.
    """
    # Create VariableCollection from module specs (base)
    module_collection = VariableCollection(module_specs) if module_specs else VariableCollection({})
    
    # Set origin for module variables
    for section in module_collection.get_sections().values():
      for variable in section.variables.values():
        if not variable.origin:
          variable.origin = "module"
    
    # Merge template specs into module specs (template overrides)
    if template_specs:
      merged_collection = module_collection.merge(template_specs, origin="template")
    else:
      merged_collection = module_collection
    
    # Convert back to dict format
    merged_spec = {}
    for section_key, section in merged_collection.get_sections().items():
      merged_spec[section_key] = section.to_dict()
    
    return merged_spec

  def _collect_template_files(self) -> None:
    """Collects all TemplateFile objects in the template directory."""
    template_files: List[TemplateFile] = []
    
    for root, _, files in os.walk(self.template_dir):
      for filename in files:
        file_path = Path(root) / filename
        relative_path = file_path.relative_to(self.template_dir)
        
        # Skip the main template file
        if filename in ["template.yaml", "template.yml"]:
          continue
        
        if filename.endswith(".j2"):
          file_type: Literal['j2', 'static'] = 'j2'
          output_path = relative_path.with_suffix('') # Remove .j2 suffix
        else:
          file_type = 'static'
          output_path = relative_path # Static files keep their name
        
        template_files.append(TemplateFile(relative_path=relative_path, file_type=file_type, output_path=output_path))
          
    self.__template_files = template_files

  def _extract_all_used_variables(self) -> Set[str]:
    """Extract all undeclared variables from all .j2 files in the template directory."""
    used_variables: Set[str] = set()
    for template_file in self.template_files: # Iterate over TemplateFile objects
      if template_file.file_type == 'j2':
        file_path = self.template_dir / template_file.relative_path
        try:
          with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            ast = self.jinja_env.parse(content) # Use lazy-loaded jinja_env
            used_variables.update(meta.find_undeclared_variables(ast))
        except Exception as e:
          logger.warning(f"Could not parse Jinja2 variables from {file_path}: {e}")
    return used_variables

  def _extract_jinja_default_values(self) -> dict[str, object]:
    """Scan all .j2 files and extract literal arguments to the `default` filter.

    Returns a mapping var_name -> literal_value for simple cases like
    {{ var | default("value") }} or {{ var | default(123) }}.
    This does not attempt to evaluate complex expressions.
    """
    defaults: dict[str, object] = {}

    class _DefaultVisitor(NodeVisitor):
      def __init__(self):
        self.found: dict[str, object] = {}

      def visit_Filter(self, node: nodes.Filter) -> None:  # type: ignore[override]
        try:
          if getattr(node, 'name', None) == 'default' and node.args:
            # target variable name when filter is applied directly to a Name
            target = None
            if isinstance(node.node, nodes.Name):
              target = node.node.name

            # first arg literal
            first = node.args[0]
            if isinstance(first, nodes.Const) and target:
              self.found[target] = first.value
        except Exception:
          # Be resilient to unexpected node shapes
          pass
        # continue traversal
        self.generic_visit(node)

    visitor = _DefaultVisitor()

    for template_file in self.template_files:
      if template_file.file_type != 'j2':
        continue
      file_path = self.template_dir / template_file.relative_path
      try:
        with open(file_path, 'r', encoding='utf-8') as f:
          content = f.read()
        ast = self.jinja_env.parse(content)
        visitor.visit(ast)
      except Exception:
        # skip failures - this extraction is best-effort only
        continue

    return visitor.found

  def _filter_specs_to_used(self, used_variables: set, merged_specs: dict, module_specs: dict, template_specs: dict) -> dict:
    """Filter specs to only include variables used in templates using VariableCollection.
    
    Uses VariableCollection's native filter_to_used() method.
    Keeps sensitive variables even if not used.
    """
    # Create VariableCollection from merged specs
    merged_collection = VariableCollection(merged_specs)
    
    # Filter to only used variables (and sensitive ones)
    filtered_collection = merged_collection.filter_to_used(used_variables, keep_sensitive=True)
    
    # Convert back to dict format
    filtered_specs = {}
    for section_key, section in filtered_collection.get_sections().items():
      filtered_specs[section_key] = section.to_dict()
    
    return filtered_specs

  # ---------------------------
  # SECTION: Validation Methods
  # ---------------------------

  @staticmethod
  def _validate_kind(template_data: dict) -> None:
    """Validate that template has required 'kind' field.
    
    Args:
        template_data: Parsed YAML data from template.yaml
        
    Raises:
        ValueError: If 'kind' field is missing
    """
    if not template_data.get("kind"):
      raise ValueError("Template format error: missing 'kind' field")

  def _validate_variable_definitions(self, used_variables: set[str], merged_specs: dict[str, Any]) -> None:
    """Validate that all variables used in Jinja2 content are defined in the spec."""
    defined_variables = set()
    for section_data in merged_specs.values():
      if "vars" in section_data and isinstance(section_data["vars"], dict):
        defined_variables.update(section_data["vars"].keys())
    
    undefined_variables = used_variables - defined_variables
    if undefined_variables:
      undefined_list = sorted(undefined_variables)
      error_msg = (
          f"Template validation error in '{self.id}': "
          f"Variables used in template content but not defined in spec: {undefined_list}\n\n"
          f"Please add these variables to your template's template.yaml spec. "
          f"Each variable must have a default value.\n\n"
          f"Example:\n"
          f"spec:\n"
          f"  general:\n"
          f"    vars:\n"
      )
      for var_name in undefined_list:
          error_msg += (
              f"      {var_name}:\n"
              f"        type: str\n"
              f"        description: Description for {var_name}\n"
              f"        default: <your_default_value_here>\n"
          )
      logger.error(error_msg)
      raise ValueError(error_msg)

  # !SECTION

  # ---------------------------------
  # SECTION: Jinja2 Rendering Methods
  # ---------------------------------

  @staticmethod
  def _create_jinja_env(searchpath: Path) -> Environment:
    """Create standardized Jinja2 environment for consistent template processing."""
    return Environment(
      loader=FileSystemLoader(searchpath),
      trim_blocks=True,
      lstrip_blocks=True,
      keep_trailing_newline=False,
    )

  def render(self, variables: VariableCollection) -> Dict[str, str]:
    """Render all .j2 files in the template directory."""
    variable_values = variables.get_all_values()
    logger.debug(f"Rendering template '{self.id}' with variables: {variable_values}")
    rendered_files = {}
    for template_file in self.template_files: # Iterate over TemplateFile objects
      if template_file.file_type == 'j2':
        try:
          template = self.jinja_env.get_template(str(template_file.relative_path)) # Use lazy-loaded jinja_env
          rendered_content = template.render(**variable_values)
          rendered_files[str(template_file.output_path)] = rendered_content
        except Exception as e:
          logger.error(f"Error rendering template file {template_file.relative_path}: {e}")
          raise
      elif template_file.file_type == 'static':
          # For static files, just read their content and add to rendered_files
          # This ensures static files are also part of the output dictionary
          file_path = self.template_dir / template_file.relative_path
          try:
              with open(file_path, "r", encoding="utf-8") as f:
                  content = f.read()
                  rendered_files[str(template_file.output_path)] = content
          except Exception as e:
              logger.error(f"Error reading static file {file_path}: {e}")
              raise
          
    return rendered_files

  def mask_sensitive_values(self, rendered_files: Dict[str, str], variables: VariableCollection) -> Dict[str, str]:
    """Mask sensitive values in rendered files using Variable's native masking."""
    masked_files = {}
    
    # Get all variables (not just sensitive ones) to use their native get_display_value()
    for file_path, content in rendered_files.items():
      # Iterate through all sections and variables
      for section in variables.get_sections().values():
        for variable in section.variables.values():
          if variable.sensitive and variable.value:
            # Use variable's native masking - always returns "********" for sensitive vars
            masked_value = variable.get_display_value(mask_sensitive=True)
            content = content.replace(str(variable.value), masked_value)
      masked_files[file_path] = content
      
    return masked_files
  
  # !SECTION

  # ---------------------------
  # SECTION: Lazy Loaded Properties
  # ---------------------------

  @property
  def template_files(self) -> List[TemplateFile]:
      if self.__template_files is None:
          self._collect_template_files() # Populate self.__template_files
      return self.__template_files

  @property
  def template_specs(self) -> dict:
      """Get the spec section from template YAML data."""
      return self._template_data.get("spec", {})

  @property
  def module_specs(self) -> dict:
      """Get the spec from the module definition."""
      if self.__module_specs is None:
          kind = self._template_data.get("kind")
          self.__module_specs = self._load_module_specs(kind)
      return self.__module_specs

  @property
  def merged_specs(self) -> dict:
      if self.__merged_specs is None:
          self.__merged_specs = self._merge_specs(self.module_specs, self.template_specs)
      return self.__merged_specs

  @property
  def jinja_env(self) -> Environment:
      if self.__jinja_env is None:
          self.__jinja_env = self._create_jinja_env(self.template_dir)
      return self.__jinja_env

  @property
  def used_variables(self) -> Set[str]:
      if self.__used_variables is None:
          self.__used_variables = self._extract_all_used_variables()
      return self.__used_variables

  @property
  def variables(self) -> VariableCollection:
      if self.__variables is None:
          # Validate that all used variables are defined
          self._validate_variable_definitions(self.used_variables, self.merged_specs)
          # Filter specs to only used variables
          filtered_specs = self._filter_specs_to_used(self.used_variables, self.merged_specs, self.module_specs, self.template_specs)

          # Best-effort: extract literal defaults from Jinja `default()` filter and
          # merge them into the filtered_specs when no default exists there.
          try:
            jinja_defaults = self._extract_jinja_default_values()
            for section_key, section_data in filtered_specs.items():
              # Guard against None from empty YAML sections
              vars_dict = section_data.get('vars') or {}
              for var_name, var_data in vars_dict.items():
                if 'default' not in var_data or var_data.get('default') in (None, ''):
                  if var_name in jinja_defaults:
                    var_data['default'] = jinja_defaults[var_name]
          except Exception:
            # keep behavior stable on any extraction errors
            pass

          self.__variables = VariableCollection(filtered_specs)
      return self.__variables