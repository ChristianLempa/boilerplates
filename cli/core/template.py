from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
import logging
import re
from jinja2 import Environment, BaseLoader, meta, nodes, TemplateSyntaxError
import frontmatter
from .exceptions import TemplateValidationError
# Module variables will be handled by the module's VariableRegistry


@dataclass
class Template:
  """Data class for template information extracted from frontmatter."""
  
  # Required fields
  file_path: Path
  content: str = ""
  
  # Frontmatter fields with defaults
  name: str = ""
  description: str = "No description available"
  author: str = ""
  date: str = ""
  version: str = ""
  module: str = ""
  tags: List[str] = field(default_factory=list)
  files: List[str] = field(default_factory=list)
  variable_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # Variable hints/tips from frontmatter
  
  # Computed properties (will be set in __post_init__)
  id: str = field(init=False)
  directory: str = field(init=False)
  relative_path: str = field(init=False)
  size: int = field(init=False)
  
  # Template variable analysis results
  vars: Set[str] = field(default_factory=set, init=False)
  var_defaults: Dict[str, Any] = field(default_factory=dict, init=False)
  def __post_init__(self):
    """Initialize computed properties after dataclass initialization."""
    # Set default name if not provided
    if not self.name:
      self.name = self.file_path.parent.name
    
    # Computed properties
    self.id = self.file_path.parent.name
    self.directory = self.file_path.parent.name
    self.relative_path = self.file_path.name
    self.size = self.file_path.stat().st_size if self.file_path.exists() else 0
    
    # Parse template variables
    self.vars, self.var_defaults = self._parse_template_variables(self.content)
  
  @staticmethod
  def _create_jinja_env() -> Environment:
    """Create standardized Jinja2 environment for consistent template processing."""
    return Environment(
      loader=BaseLoader(),
      trim_blocks=True,           # Remove first newline after block tags
      lstrip_blocks=True,         # Strip leading whitespace from block tags  
      keep_trailing_newline=False  # Remove trailing newlines
    )

  @classmethod
  def from_file(cls, file_path: Path) -> "Template":
    """Create a Template instance from a file path."""
    try:
      frontmatter_data, content = cls._parse_frontmatter(file_path)
      return cls(
        file_path=file_path,
        content=content,
        name=frontmatter_data.get('name', ''),
        description=frontmatter_data.get('description', 'No description available'),
        author=frontmatter_data.get('author', ''),
        date=frontmatter_data.get('date', ''),
        version=frontmatter_data.get('version', ''),
        module=frontmatter_data.get('module', ''),
        tags=frontmatter_data.get('tags', []),
        files=frontmatter_data.get('files', []),
        variable_metadata=frontmatter_data.get('variables', {})
      )
    except Exception:
      # If frontmatter parsing fails, create a basic Template object
      return cls(file_path=file_path)
  
  @staticmethod
  def _parse_frontmatter(file_path: Path) -> Tuple[Dict[str, Any], str]:
    """Parse frontmatter and content from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
      post = frontmatter.load(f)
    return post.metadata, post.content
  
  def _parse_template_variables(self, template_content: str) -> Tuple[Set[str], Dict[str, Any]]:
    """Parse Jinja2 template to extract variables and their defaults.
    
    Handles:
    - Simple variables: service_name
    - Dotted notation: traefik.host, service_port.http
    
    Returns:
        Tuple of (all_variable_names, variable_defaults)
    """
    try:
      env = self._create_jinja_env()
      ast = env.parse(template_content)
      
      # Start with variables found by Jinja2's meta utility
      all_variables = meta.find_undeclared_variables(ast)
      
      # Handle dotted notation variables (like traefik.host, service_port.http)
      for node in ast.find_all(nodes.Getattr):
        current = node.node
        # Build the full dotted name
        parts = [node.attr]
        while isinstance(current, nodes.Getattr):
          parts.insert(0, current.attr)
          current = current.node
        if isinstance(current, nodes.Name):
          parts.insert(0, current.name)
          # Add the full dotted variable name
          all_variables.add('.'.join(parts))
      
      # Extract default values from | default() filters
      defaults = {}
      for node in ast.find_all(nodes.Filter):
        if node.name == 'default' and node.args and isinstance(node.args[0], nodes.Const):
          # Handle simple variable defaults: {{ var | default(value) }}
          if isinstance(node.node, nodes.Name):
            defaults[node.node.name] = node.args[0].value
          
          # Handle dotted variable defaults: {{ traefik.host | default('example.com') }}
          elif isinstance(node.node, nodes.Getattr):
            # Build the full dotted name
            current = node.node
            parts = []
            while isinstance(current, nodes.Getattr):
              parts.insert(0, current.attr)
              current = current.node
            if isinstance(current, nodes.Name):
              parts.insert(0, current.name)
              var_name = '.'.join(parts)
              defaults[var_name] = node.args[0].value
      
      return all_variables, defaults
    except Exception as e:
      logging.getLogger('boilerplates').debug(f"Error parsing template variables: {e}")
      return set(), {}

  def validate(self, module_variable_registry=None, template_id: str = None):
    """Validate template integrity.
    
    Args:
        module_variable_registry: Module's VariableRegistry for validation
        template_id: Template ID for error messages (uses self.id if not provided)
    
    Raises:
        TemplateValidationError: If validation fails.
    """
    import logging
    from .exceptions import TemplateValidationError
    
    logger = logging.getLogger('boilerplates')
    template_id = template_id or self.id
    errors = []
    warnings = []
    
    # Check for Jinja2 syntax errors (critical)
    try:
      env = self._create_jinja_env()
      env.from_string(self.content)
    except TemplateSyntaxError as e:
      raise TemplateValidationError(template_id, [f"Invalid Jinja2 syntax at line {e.lineno}: {e.message}"])
    except Exception as e:
      raise TemplateValidationError(template_id, [f"Template parsing error: {str(e)}"])
    
    # Validate module variable registry consistency
    if module_variable_registry:
      registry_errors = module_variable_registry.validate_parent_child_relationships()
      if registry_errors:
        errors.extend(registry_errors)
    
    # Validate variable definitions (critical)
    undefined_vars = self._validate_variable_definitions(module_variable_registry)
    if undefined_vars:
      errors.extend(undefined_vars)
    
    # Check for missing frontmatter fields (warnings)
    if not self.name:
      warnings.append("Missing 'name' in frontmatter")
    
    if not self.description or self.description == 'No description available':
      warnings.append("Missing 'description' in frontmatter")
    
    # Check for empty content (warning)
    if not self.content.strip() and not self.files:
      warnings.append("Template has no content")
    
    # Raise if critical errors found
    if errors:
      raise TemplateValidationError(template_id, errors)
    
    # Log warnings
    for warning in warnings:
      logger.warning(f"Template '{template_id}': {warning}")

  def _validate_variable_definitions(self, module_variable_registry) -> List[str]:
    """Validate that all template variables are properly defined.
    
    Args:
        module_variable_registry: Module's VariableRegistry instance
    
    Returns:
        List of error messages for undefined variables
    """
    errors = []
    
    if not module_variable_registry:
      return errors
    
    # Check that all template variables are either registered or in frontmatter
    unregistered_vars = []
    for var_name in self.vars:
      # Check if variable is registered in module
      if not module_variable_registry.get_variable(var_name):
        # Check if it's defined in template's frontmatter
        if var_name not in self.variable_metadata:
          unregistered_vars.append(var_name)
    
    if unregistered_vars:
      errors.append(
        f"Unregistered variables found: {', '.join(unregistered_vars)}. "
        f"Variables must be either registered in the module or defined in template frontmatter 'variables' section."
      )
    
    return errors

  def render(self, variable_values: Dict[str, Any]) -> str:
    """Render the template with the provided variable values."""
    logger = logging.getLogger('boilerplates')
    
    try:
      env = self._create_jinja_env()
      jinja_template = env.from_string(self.content)
      # Merge template defaults with provided values
      # All variables should be defined at this point due to validation
      merged_variable_values = {**self.var_defaults, **variable_values}
      rendered_content = jinja_template.render(**merged_variable_values)
      
      # Clean up excessive blank lines and whitespace
      rendered_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', rendered_content)
      return rendered_content.strip()
      
    except Exception as e:
      logger.error(f"Jinja2 template rendering failed: {e}")
      raise ValueError(f"Failed to render template: {e}")
