from __future__ import annotations

from .variable import Variable
from .collection import VariableCollection
from .exceptions import (
    TemplateError,
    TemplateLoadError,
    TemplateSyntaxError,
    TemplateValidationError,
    TemplateRenderError,
    YAMLParseError,
    ModuleLoadError,
    IncompatibleSchemaVersionError
)
from .version import is_compatible
from pathlib import Path
from typing import Any, Dict, List, Set, Optional, Literal
from dataclasses import dataclass, field
from functools import lru_cache
import logging
import os
import yaml
from jinja2 import Environment, FileSystemLoader, meta
from jinja2.sandbox import SandboxedEnvironment
from jinja2 import nodes
from jinja2.visitor import NodeVisitor
from jinja2.exceptions import (
    TemplateSyntaxError as Jinja2TemplateSyntaxError,
    UndefinedError,
    TemplateError as Jinja2TemplateError,
    TemplateNotFound as Jinja2TemplateNotFound
)

logger = logging.getLogger(__name__)


def _extract_error_context(
    file_path: Path,
    line_number: Optional[int],
    context_size: int = 3
) -> List[str]:
  """Extract lines of context around an error location.
  
  Args:
      file_path: Path to the file with the error
      line_number: Line number where error occurred (1-indexed)
      context_size: Number of lines to show before and after
      
  Returns:
      List of context lines with line numbers
  """
  if not line_number or not file_path.exists():
    return []
  
  try:
    with open(file_path, 'r', encoding='utf-8') as f:
      lines = f.readlines()
    
    start_line = max(0, line_number - context_size - 1)
    end_line = min(len(lines), line_number + context_size)
    
    context = []
    for i in range(start_line, end_line):
      line_num = i + 1
      marker = '>>>' if line_num == line_number else '   '
      context.append(f"{marker} {line_num:4d} | {lines[i].rstrip()}")
    
    return context
  except (IOError, OSError):
    return []


def _get_common_jinja_suggestions(error_msg: str, available_vars: set) -> List[str]:
  """Generate helpful suggestions based on common Jinja2 errors.
  
  Args:
      error_msg: The error message from Jinja2
      available_vars: Set of available variable names
      
  Returns:
      List of actionable suggestions
  """
  suggestions = []
  error_lower = error_msg.lower()
  
  # Undefined variable errors
  if 'undefined' in error_lower or 'is not defined' in error_lower:
    # Try to extract variable name from error message
    import re
    var_match = re.search(r"'([^']+)'.*is undefined", error_msg)
    if not var_match:
      var_match = re.search(r"'([^']+)'.*is not defined", error_msg)
    
    if var_match:
      undefined_var = var_match.group(1)
      suggestions.append(f"Variable '{undefined_var}' is not defined in the template spec")
      
      # Suggest similar variable names (basic fuzzy matching)
      similar = [v for v in available_vars if undefined_var.lower() in v.lower() or v.lower() in undefined_var.lower()]
      if similar:
        suggestions.append(f"Did you mean one of these? {', '.join(sorted(similar)[:5])}")
      
      suggestions.append(f"Add '{undefined_var}' to your template.yaml spec with a default value")
      suggestions.append("Or use the Jinja2 default filter: {{ " + undefined_var + " | default('value') }}")
    else:
      suggestions.append("Check that all variables used in templates are defined in template.yaml")
      suggestions.append("Use the Jinja2 default filter for optional variables: {{ var | default('value') }}")
  
  # Syntax errors
  elif 'unexpected' in error_lower or 'expected' in error_lower:
    suggestions.append("Check for syntax errors in your Jinja2 template")
    suggestions.append("Common issues: missing {% endfor %}, {% endif %}, or {% endblock %}")
    suggestions.append("Make sure all {{ }} and {% %} tags are properly closed")
  
  # Filter errors
  elif 'filter' in error_lower:
    suggestions.append("Check that the filter name is spelled correctly")
    suggestions.append("Verify the filter exists in Jinja2 built-in filters")
    suggestions.append("Make sure filter arguments are properly formatted")
  
  # Template not found
  elif 'not found' in error_lower or 'does not exist' in error_lower:
    suggestions.append("Check that the included/imported template file exists")
    suggestions.append("Verify the template path is relative to the template directory")
    suggestions.append("Make sure the file has the .j2 extension if it's a Jinja2 template")
  
  # Type errors
  elif 'type' in error_lower and ('int' in error_lower or 'str' in error_lower or 'bool' in error_lower):
    suggestions.append("Check that variable values have the correct type")
    suggestions.append("Use Jinja2 filters to convert types: {{ var | int }}, {{ var | string }}")
  
  # Add generic helpful tip
  if not suggestions:
    suggestions.append("Check the Jinja2 template syntax and variable usage")
    suggestions.append("Enable --debug mode for more detailed rendering information")
  
  return suggestions


def _parse_jinja_error(
    error: Exception,
    template_file: TemplateFile,
    template_dir: Path,
    available_vars: set
) -> tuple[str, Optional[int], Optional[int], List[str], List[str]]:
  """Parse a Jinja2 exception to extract detailed error information.
  
  Args:
      error: The Jinja2 exception
      template_file: The TemplateFile being rendered
      template_dir: Template directory path
      available_vars: Set of available variable names
      
  Returns:
      Tuple of (error_message, line_number, column, context_lines, suggestions)
  """
  error_msg = str(error)
  line_number = None
  column = None
  context_lines = []
  suggestions = []
  
  # Extract line number from Jinja2 errors
  if hasattr(error, 'lineno'):
    line_number = error.lineno
  
  # Extract file path and get context
  file_path = template_dir / template_file.relative_path
  if line_number and file_path.exists():
    context_lines = _extract_error_context(file_path, line_number)
  
  # Generate suggestions based on error type
  if isinstance(error, UndefinedError):
    error_msg = f"Undefined variable: {error}"
    suggestions = _get_common_jinja_suggestions(str(error), available_vars)
  elif isinstance(error, Jinja2TemplateSyntaxError):
    error_msg = f"Template syntax error: {error}"
    suggestions = _get_common_jinja_suggestions(str(error), available_vars)
  elif isinstance(error, Jinja2TemplateNotFound):
    error_msg = f"Template file not found: {error}"
    suggestions = _get_common_jinja_suggestions(str(error), available_vars)
  else:
    # Generic Jinja2 error
    suggestions = _get_common_jinja_suggestions(error_msg, available_vars)
  
  return error_msg, line_number, column, context_lines, suggestions


@dataclass
class TemplateFile:
    """Represents a single file within a template directory."""
    relative_path: Path
    file_type: Literal['j2', 'static']
    output_path: Path # The path it will have in the output directory

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
  library: str = "unknown"
  library_type: str = "git"  # Type of library ("git" or "static")
  next_steps: str = ""
  draft: bool = False

  def __init__(self, template_data: dict, library_name: str | None = None, library_type: str = "git") -> None:
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
    self.library = library_name or "unknown"
    self.library_type = library_type
    self.draft = metadata_section.get("draft", False)
    
    # Extract next_steps (optional)
    raw_next_steps = metadata_section.get("next_steps", "")
    if isinstance(raw_next_steps, str):
      next_steps = raw_next_steps.rstrip("\n")
    else:
      next_steps = str(raw_next_steps) if raw_next_steps else ""
    self.next_steps = next_steps

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

@dataclass
class Template:
  """Represents a template directory."""

  def __init__(self, template_dir: Path, library_name: str, library_type: str = "git") -> None:
    """Create a Template instance from a directory path.
    
    Args:
        template_dir: Path to the template directory
        library_name: Name of the library this template belongs to
        library_type: Type of library ("git" or "static"), defaults to "git"
    """
    logger.debug(f"Loading template from directory: {template_dir}")
    self.template_dir = template_dir
    self.id = template_dir.name
    self.original_id = template_dir.name  # Store the original ID
    self.library_name = library_name
    self.library_type = library_type

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
      self.metadata = TemplateMetadata(self._template_data, library_name, library_type)
      logger.debug(f"Loaded metadata: {self.metadata}")

      # Validate 'kind' field (always needed)
      self._validate_kind(self._template_data)
      
      # Extract schema version (default to 1.0 for backward compatibility)
      self.schema_version = str(self._template_data.get("schema", "1.0"))
      logger.debug(f"Template schema version: {self.schema_version}")
      
      # Note: Schema version validation is done by the module when loading templates

      # NOTE: File collection is now lazy-loaded via the template_files property
      # This significantly improves performance when listing many templates

      logger.info(f"Loaded template '{self.id}' (v{self.metadata.version})")

    except (ValueError, FileNotFoundError) as e:
      logger.error(f"Error loading template from {template_dir}: {e}")
      raise TemplateLoadError(f"Error loading template from {template_dir}: {e}")
    except yaml.YAMLError as e:
      logger.error(f"YAML parsing error in template {template_dir}: {e}")
      raise YAMLParseError(str(template_dir / "template.y*ml"), e)
    except (IOError, OSError) as e:
      logger.error(f"File I/O error loading template {template_dir}: {e}")
      raise TemplateLoadError(f"File I/O error loading template from {template_dir}: {e}")

  def set_qualified_id(self, library_name: str | None = None) -> None:
    """Set a qualified ID for this template (used when duplicates exist across libraries).
    
    Args:
        library_name: Name of the library to qualify with. If None, uses self.library_name
    """
    lib_name = library_name or self.library_name
    self.id = f"{self.original_id}.{lib_name}"
    logger.debug(f"Template ID qualified: {self.original_id} -> {self.id}")

  def _find_main_template_file(self) -> Path:
    """Find the main template file (template.yaml or template.yml)."""
    for filename in ["template.yaml", "template.yml"]:
      path = self.template_dir / filename
      if path.exists():
        return path
    raise FileNotFoundError(f"Main template file (template.yaml or template.yml) not found in {self.template_dir}")

  @staticmethod
  @lru_cache(maxsize=32)
  def _load_module_specs(kind: str) -> dict:
    """Load specifications from the corresponding module with caching.
    
    Uses LRU cache to avoid re-loading the same module spec multiple times.
    This significantly improves performance when listing many templates of the same kind.
    
    Args:
        kind: The module kind (e.g., 'compose', 'terraform')
        
    Returns:
        Dictionary containing the module's spec, or empty dict if kind is empty
        
    Raises:
        ValueError: If module cannot be loaded or spec is invalid
    """
    if not kind:
      return {}
    try:
      import importlib
      module = importlib.import_module(f"cli.modules.{kind}")
      spec = getattr(module, 'spec', {})
      logger.debug(f"Loaded and cached module spec for kind '{kind}'")
      return spec
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
    """Extract all undeclared variables from all .j2 files in the template directory.
    
    Raises:
        ValueError: If any Jinja2 template has syntax errors
    """
    used_variables: Set[str] = set()
    syntax_errors = []
    
    for template_file in self.template_files: # Iterate over TemplateFile objects
      if template_file.file_type == 'j2':
        file_path = self.template_dir / template_file.relative_path
        try:
          with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            ast = self.jinja_env.parse(content) # Use lazy-loaded jinja_env
            used_variables.update(meta.find_undeclared_variables(ast))
        except (IOError, OSError) as e:
          relative_path = file_path.relative_to(self.template_dir)
          syntax_errors.append(f"  - {relative_path}: File I/O error: {e}")
        except Exception as e:
          # Collect syntax errors for Jinja2 issues
          relative_path = file_path.relative_to(self.template_dir)
          syntax_errors.append(f"  - {relative_path}: {e}")
    
    # Raise error if any syntax errors were found
    if syntax_errors:
      logger.error(f"Jinja2 syntax errors found in template '{self.id}'")
      raise TemplateSyntaxError(self.id, syntax_errors)
    
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
      except (IOError, OSError, yaml.YAMLError):
        # Skip failures - this extraction is best-effort only
        continue

    return visitor.found

  def _filter_specs_to_used(self, used_variables: set, merged_specs: dict, module_specs: dict, template_specs: dict) -> dict:
    """Filter specs to only include variables used in templates using VariableCollection.
    
    Uses VariableCollection's native filter_to_used() method.
    Keeps sensitive variables only if they're defined in the template spec or actually used.
    """
    # Build set of variables explicitly defined in template spec
    template_defined_vars = set()
    for section_data in (template_specs or {}).values():
      if isinstance(section_data, dict) and 'vars' in section_data:
        template_defined_vars.update(section_data['vars'].keys())
    
    # Create VariableCollection from merged specs
    merged_collection = VariableCollection(merged_specs)
    
    # Filter to only used variables (and sensitive ones that are template-defined)
    # We keep sensitive variables that are either:
    # 1. Actually used in template files, OR
    # 2. Explicitly defined in the template spec (even if not yet used)
    variables_to_keep = used_variables | template_defined_vars
    filtered_collection = merged_collection.filter_to_used(variables_to_keep, keep_sensitive=False)
    
    # Convert back to dict format
    filtered_specs = {}
    for section_key, section in filtered_collection.get_sections().items():
      filtered_specs[section_key] = section.to_dict()
    
    return filtered_specs

  def _validate_schema_version(self, module_schema: str, module_name: str) -> None:
    """Validate that template schema version is supported by the module.
    
    Args:
        module_schema: Schema version supported by the module
        module_name: Name of the module (for error messages)
    
    Raises:
        IncompatibleSchemaVersionError: If template schema > module schema
    """
    template_schema = self.schema_version
    
    # Compare schema versions
    if not is_compatible(module_schema, template_schema):
      logger.error(
        f"Template '{self.id}' uses schema version {template_schema}, "
        f"but module '{module_name}' only supports up to {module_schema}"
      )
      raise IncompatibleSchemaVersionError(
        template_id=self.id,
        template_schema=template_schema,
        module_schema=module_schema,
        module_name=module_name
      )
    
    logger.debug(
      f"Template '{self.id}' schema version compatible: "
      f"template uses {template_schema}, module supports {module_schema}"
    )
  
  @staticmethod
  def _validate_kind(template_data: dict) -> None:
    """Validate that template has required 'kind' field.
    
    Args:
        template_data: Parsed YAML data from template.yaml
        
    Raises:
        ValueError: If 'kind' field is missing
    """
    if not template_data.get("kind"):
      raise TemplateValidationError("Template format error: missing 'kind' field")

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
      raise TemplateValidationError(error_msg)

  @staticmethod
  def _create_jinja_env(searchpath: Path) -> Environment:
    """Create sandboxed Jinja2 environment for secure template processing.
    
    Uses SandboxedEnvironment to prevent code injection vulnerabilities
    when processing untrusted templates. This restricts access to dangerous
    operations while still allowing safe template rendering.
    
    Returns:
        SandboxedEnvironment configured for template processing.
    """
    # NOTE Use SandboxedEnvironment for security - prevents arbitrary code execution
    return SandboxedEnvironment(
      loader=FileSystemLoader(searchpath),
      trim_blocks=True,
      lstrip_blocks=True,
      keep_trailing_newline=False,
    )

  def render(self, variables: VariableCollection, debug: bool = False) -> tuple[Dict[str, str], Dict[str, Any]]:
    """Render all .j2 files in the template directory.
    
    Args:
        variables: VariableCollection with values to use for rendering
        debug: Enable debug mode with verbose output
        
    Returns:
        Tuple of (rendered_files, variable_values) where variable_values includes autogenerated values
    """
    # Use get_satisfied_values() to exclude variables from sections with unsatisfied dependencies
    variable_values = variables.get_satisfied_values()
    
    # Auto-generate values for autogenerated variables that are empty
    import secrets
    import string
    for section in variables.get_sections().values():
      for var_name, variable in section.variables.items():
        if variable.autogenerated and (variable.value is None or variable.value == ""):
          # Generate a secure random string (32 characters by default)
          alphabet = string.ascii_letters + string.digits
          generated_value = ''.join(secrets.choice(alphabet) for _ in range(32))
          variable_values[var_name] = generated_value
          logger.debug(f"Auto-generated value for variable '{var_name}'")
    
    if debug:
      logger.info(f"Rendering template '{self.id}' in debug mode")
      logger.info(f"Available variables: {sorted(variable_values.keys())}")
      logger.info(f"Variable values: {variable_values}")
    else:
      logger.debug(f"Rendering template '{self.id}' with variables: {variable_values}")
    
    rendered_files = {}
    available_vars = set(variable_values.keys())
    
    for template_file in self.template_files: # Iterate over TemplateFile objects
      if template_file.file_type == 'j2':
        try:
          if debug:
            logger.info(f"Rendering Jinja2 template: {template_file.relative_path}")
          
          template = self.jinja_env.get_template(str(template_file.relative_path)) # Use lazy-loaded jinja_env
          rendered_content = template.render(**variable_values)
          
          # Sanitize the rendered content to remove excessive blank lines
          rendered_content = self._sanitize_content(rendered_content, template_file.output_path)
          rendered_files[str(template_file.output_path)] = rendered_content
          
          if debug:
            logger.info(f"Successfully rendered: {template_file.relative_path} -> {template_file.output_path}")
        
        except (UndefinedError, Jinja2TemplateSyntaxError, Jinja2TemplateNotFound, Jinja2TemplateError) as e:
          # Parse Jinja2 error to extract detailed information
          error_msg, line_num, col, context_lines, suggestions = _parse_jinja_error(
              e, template_file, self.template_dir, available_vars
          )
          
          logger.error(f"Error rendering template file {template_file.relative_path}: {error_msg}")
          
          # Create enhanced TemplateRenderError with all context
          raise TemplateRenderError(
              message=error_msg,
              file_path=str(template_file.relative_path),
              line_number=line_num,
              column=col,
              context_lines=context_lines,
              variable_context={k: str(v) for k, v in variable_values.items()} if debug else {},
              suggestions=suggestions,
              original_error=e
          )
        
        except Exception as e:
          # Catch any other unexpected errors
          logger.error(f"Unexpected error rendering template file {template_file.relative_path}: {e}")
          raise TemplateRenderError(
              message=f"Unexpected rendering error: {e}",
              file_path=str(template_file.relative_path),
              suggestions=["This is an unexpected error. Please check the template for issues."],
              original_error=e
          )
      
      elif template_file.file_type == 'static':
          # For static files, just read their content and add to rendered_files
          # This ensures static files are also part of the output dictionary
          file_path = self.template_dir / template_file.relative_path
          try:
              if debug:
                logger.info(f"Copying static file: {template_file.relative_path}")
              
              with open(file_path, "r", encoding="utf-8") as f:
                  content = f.read()
                  rendered_files[str(template_file.output_path)] = content
          except (IOError, OSError) as e:
              logger.error(f"Error reading static file {file_path}: {e}")
              raise TemplateRenderError(
                  message=f"Error reading static file: {e}",
                  file_path=str(template_file.relative_path),
                  suggestions=["Check that the file exists and has read permissions"],
                  original_error=e
              )
          
    return rendered_files, variable_values
  
  def _sanitize_content(self, content: str, file_path: Path) -> str:
    """Sanitize rendered content by removing excessive blank lines and trailing whitespace."""
    if not content:
      return content
    
    lines = [line.rstrip() for line in content.split('\n')]
    sanitized = []
    prev_blank = False
    
    for line in lines:
      is_blank = not line
      if is_blank and prev_blank:
        continue  # Skip consecutive blank lines
      sanitized.append(line)
      prev_blank = is_blank
    
    # Remove leading blanks and ensure single trailing newline
    return '\n'.join(sanitized).lstrip('\n').rstrip('\n') + '\n'

  
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
          except (KeyError, TypeError, AttributeError):
            # Keep behavior stable on any extraction errors
            pass

          self.__variables = VariableCollection(filtered_specs)
          # Sort sections: required first, then enabled, then disabled
          self.__variables.sort_sections()
      return self.__variables
