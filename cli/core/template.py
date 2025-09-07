from pathlib import Path
from typing import Any, Dict, Set, Tuple, List
import logging
import re
from jinja2 import Environment, BaseLoader, meta, nodes, TemplateSyntaxError
import frontmatter
from .exceptions import TemplateValidationError


class Template:
  """Data class for template information extracted from frontmatter."""
  
  @staticmethod
  def _create_jinja_env() -> Environment:
    """Create standardized Jinja2 environment for consistent template processing."""
    return Environment(
      loader=BaseLoader(),
      trim_blocks=True,           # Remove first newline after block tags
      lstrip_blocks=True,         # Strip leading whitespace from block tags  
      keep_trailing_newline=False  # Remove trailing newlines
    )
  
  def __init__(self, file_path: Path, frontmatter_data: Dict[str, Any], content: str):
    self.file_path = file_path
    self.content = content
    
    # Extract frontmatter fields with defaults
    self.name = frontmatter_data.get('name', file_path.parent.name)  # Use directory name as default
    self.description = frontmatter_data.get('description', 'No description available')
    self.author = frontmatter_data.get('author', '')
    self.date = frontmatter_data.get('date', '')
    self.version = frontmatter_data.get('version', '')
    self.module = frontmatter_data.get('module', '')
    self.tags = frontmatter_data.get('tags', [])
    self.files = frontmatter_data.get('files', [])
    
    # Additional computed properties
    self.id = file_path.parent.name  # Unique identifier (parent directory name)
    self.directory = file_path.parent.name  # Directory name where the template is located
    self.relative_path = file_path.name
    self.size = file_path.stat().st_size if file_path.exists() else 0
    
    # Extract variables and defaults from the template content
    # vars: Set[str] - All Jinja2 variable names found in template (e.g., {'app_name', 'port', 'debug'})
    # var_defaults: Dict[str, Any] - Default values from | default() filters (e.g., {'app_name': 'my-app', 'port': 8080})
    # var_usage: Dict[str, Dict] - How variables are used (simple, array indices, dict keys)
    self.vars, self.var_defaults, self.var_usage = self._parse_template_variables(content)

  @classmethod
  def from_file(cls, file_path: Path) -> "Template":
    """Create a Template instance from a file path."""
    try:
      frontmatter_data, content = cls._parse_frontmatter(file_path)
      return cls(file_path=file_path, frontmatter_data=frontmatter_data, content=content)
    except Exception:
      # If frontmatter parsing fails, create a basic Template object
      return cls(
        file_path=file_path,
        frontmatter_data={'name': file_path.parent.name},
        content=""
      )
  
  @staticmethod
  def _parse_frontmatter(file_path: Path) -> Tuple[Dict[str, Any], str]:
    """Parse frontmatter and content from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
      post = frontmatter.load(f)
    return post.metadata, post.content
  
  def _parse_template_variables(self, template_content: str) -> Tuple[Set[str], Dict[str, Any], Dict[str, Dict]]:
    """Parse Jinja2 template to extract variables, defaults, and usage patterns.
    
    Examples:
        {{ app_name | default('my-app') }} → Simple variable
        {{ service_port['http'] }} → Dict with key 'http'
        {{ service_port.https }} → Dict with key 'https' (dot notation)
        {{ docker_network[0] }} → Array with index 0
        {{ ports[item.name] }} → Dynamic dict key
    
    Returns:
        Tuple of (all_variable_names, variable_defaults, variable_usage_patterns)
    """
    try:
      env = self._create_jinja_env()
      ast = env.parse(template_content)
      
      # Start with variables found by Jinja2's meta utility
      all_variables = meta.find_undeclared_variables(ast)
      
      # Add variables used in Getattr and Getitem nodes
      for node in ast.find_all((nodes.Getattr, nodes.Getitem)):
          current_node = node.node
          while isinstance(current_node, (nodes.Getattr, nodes.Getitem)):
              current_node = current_node.node
          if isinstance(current_node, nodes.Name):
              all_variables.add(current_node.name)
      
      # Extract default values from | default() filters
      defaults = {}
      for node in ast.find_all(nodes.Filter):
        if node.name == 'default' and node.args and isinstance(node.args[0], nodes.Const):
          # Handle simple variable defaults: {{ var | default(value) }}
          if isinstance(node.node, nodes.Name):
            defaults[node.node.name] = node.args[0].value
          # Handle dict access defaults: {{ var['key'] | default(value) }}
          elif isinstance(node.node, nodes.Getitem):
            if isinstance(node.node.node, nodes.Name) and isinstance(node.node.arg, nodes.Const):
              var_name = node.node.node.name
              key = node.node.arg.value
              if var_name not in defaults:
                defaults[var_name] = {}
              if not isinstance(defaults[var_name], dict):
                defaults[var_name] = {}
              defaults[var_name][key] = node.args[0].value
      
      # Analyze variable usage patterns for multivalue support
      usage_patterns = self._analyze_variable_patterns(template_content)
      
      return all_variables, defaults, usage_patterns
    except Exception as e:
      logging.getLogger('boilerplates').debug(f"Error parsing template variables: {e}")
      return set(), {}, {}
  
  def _analyze_variable_patterns(self, template_content: str) -> Dict[str, Dict]:
    """Analyze how variables are used in the template to detect multivalue patterns.
    
    Returns a dict mapping variable names to their usage info:
    {
      'service_port': {
        'keys': ['http', 'https'],  # Keys used with this variable
        'indices': [],               # Numeric indices used
      }
    }
    """
    patterns = {}
    
    # Pattern for dict access: variable['key'] or variable["key"]
    dict_pattern = r'{{\s*(\w+)\[[\'"]([\w-]+)[\'"]\]'
    for match in re.finditer(dict_pattern, template_content):
      var_name, key = match.groups()
      if var_name not in patterns:
        patterns[var_name] = {'keys': [], 'indices': []}
      if key not in patterns[var_name]['keys']:
        patterns[var_name]['keys'].append(key)
    
    # Pattern for numeric index: variable[0], variable[1], etc.
    index_pattern = r'{{\s*(\w+)\[(\d+)\]'
    for match in re.finditer(index_pattern, template_content):
      var_name, index = match.groups()
      if var_name not in patterns:
        patterns[var_name] = {'keys': [], 'indices': []}
      idx = int(index)
      if idx not in patterns[var_name]['indices']:
        patterns[var_name]['indices'].append(idx)
    
    # Sort indices if present
    for var_name in patterns:
      patterns[var_name]['indices'].sort()
    
    return patterns

  def validate(self, registered_variables=None):
    """Validate template integrity.
    
    Args:
        registered_variables: Optional set of variable names registered by the module.
                             If provided, checks for undefined variables.
    
    Returns:
        List of validation error messages. Empty list if valid.
    """
    errors = []
    
    # Check for Jinja2 syntax errors
    try:
      env = self._create_jinja_env()
      env.from_string(self.content)
    except TemplateSyntaxError as e:
      errors.append(f"Invalid Jinja2 syntax at line {e.lineno}: {e.message}")
    except Exception as e:
      errors.append(f"Template parsing error: {str(e)}")
    
    # Check for undefined variables if registered variables are provided
    if registered_variables is not None:
      # Variables that are used in template but not defined anywhere
      undefined = self.vars - set(self.var_defaults.keys()) - registered_variables
      if undefined:
        var_list = ", ".join(sorted(undefined))
        errors.append(f"Undefined variables: {var_list}")
    
    # Check for missing required frontmatter fields
    if not self.name or self.name == self.file_path.parent.name:
      errors.append("Missing 'name' in frontmatter")
    
    if not self.description or self.description == 'No description available':
      errors.append("Missing 'description' in frontmatter")
    
    # Check for empty content (unless it's intentionally a metadata-only template)
    if not self.content.strip() and not self.files:
      errors.append("Template has no content")
    
    return errors
  
  def validate_strict(self, registered_variables=None):
    """Validate template and raise exception if invalid.
    
    Args:
        registered_variables: Optional set of variable names registered by the module.
    
    Raises:
        TemplateValidationError: If validation fails
    """
    errors = self.validate(registered_variables)
    if errors:
      raise TemplateValidationError(self.id, errors)

  def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary for display."""
    return {
      'id': self.id,
      'name': self.name,
      'description': self.description,
      'author': self.author,
      'date': self.date,
      'version': self.version,
      'module': self.module,
      'tags': self.tags,
      'files': self.files,
      'directory': self.directory,
      'path': str(self.relative_path),
      'size': f"{self.size:,} bytes",
      'vars': list(self.vars),
      'var_defaults': self.var_defaults
    }

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
