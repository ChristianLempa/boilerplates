from __future__ import annotations

from .variables import Variable, VariableCollection
from pathlib import Path
from typing import Any, Dict, List, Set, Optional, Literal
from dataclasses import dataclass, field
import logging
import os
from jinja2 import Environment, FileSystemLoader, meta
import frontmatter

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
    # self.files = metadata_section.get("files", []) or [] # No longer needed
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
        self._post = frontmatter.load(f) # Store post for later access to spec

      # Load metadata (always needed)
      self.metadata = TemplateMetadata(self._post, library_name)
      logger.debug(f"Loaded metadata: {self.metadata}")

      # Validate 'kind' field (always needed)
      self._validate_kind(self._post)

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
    """Deep merge template specs with module specs."""
    merged_specs = {}
    for section_key in module_specs.keys():
      module_section = module_specs.get(section_key, {})
      template_section = template_specs.get(section_key, {})
      merged_section = {**module_section}
      for key in ['title', 'prompt', 'description', 'toggle', 'required']:
        if key in template_section:
          merged_section[key] = template_section[key]
      module_vars = module_section.get('vars') if isinstance(module_section.get('vars'), dict) else {}
      template_vars = template_section.get('vars') if isinstance(template_section.get('vars'), dict) else {}
      merged_section['vars'] = {**module_vars, **template_vars}
      merged_specs[section_key] = merged_section
    
    for section_key in template_specs.keys():
      if section_key not in module_specs:
        merged_specs[section_key] = {**template_specs[section_key]}
        
    return merged_specs

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

  def _filter_specs_to_used(self, used_variables: set, merged_specs: dict, module_specs: dict, template_specs: dict) -> dict:
    """Filter specs to only include variables used in the templates."""
    filtered_specs = {}
    for section_key, section_data in merged_specs.items():
      if "vars" in section_data and isinstance(section_data["vars"], dict):
        filtered_vars = {}
        for var_name, var_data in section_data["vars"].items():
          if var_name in used_variables:
            module_has_var = var_name in module_specs.get(section_key, {}).get("vars", {})
            template_has_var = var_name in template_specs.get(section_key, {}).get("vars", {})
            
            if module_has_var and template_has_var:
              origin = "module -> template"
            elif template_has_var:
              origin = "template"
            else:
              origin = "module"
            
            var_data_with_origin = {**var_data, "origin": origin}
            
            filtered_vars[var_name] = var_data_with_origin
        
        if filtered_vars:
          filtered_specs[section_key] = {**section_data, "vars": filtered_vars}
    return filtered_specs

  # ---------------------------
  # SECTION: Validation Methods
  # ---------------------------

  @staticmethod
  def _validate_kind(post: frontmatter.Post) -> None:
    """Validate that template has required 'kind' field."""
    if not post.metadata.get("kind"):
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

  def render(self, variables: dict[str, Any]) -> Dict[str, str]:
    """Render all .j2 files in the template directory."""
    logger.debug(f"Rendering template '{self.id}' with variables: {variables}")
    rendered_files = {}
    for template_file in self.template_files: # Iterate over TemplateFile objects
      if template_file.file_type == 'j2':
        try:
          template = self.jinja_env.get_template(str(template_file.relative_path)) # Use lazy-loaded jinja_env
          rendered_content = template.render(**variables)
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
      return self._post.metadata.get("spec", {})

  @property
  def module_specs(self) -> dict:
      if self.__module_specs is None:
          kind = self._post.metadata.get("kind")
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
          self.__variables = VariableCollection(filtered_specs)
      return self.__variables