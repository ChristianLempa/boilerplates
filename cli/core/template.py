from pathlib import Path
from typing import Any, Dict, Set, Tuple
import logging
import re
from jinja2 import Environment, BaseLoader, meta, nodes
import frontmatter


class Template:
  """Data class for template information extracted from frontmatter."""
  
  @staticmethod
  def _create_jinja_env() -> Environment:
    """Create standardized Jinja2 environment for consistent template processing."""
    return Environment(
      loader=BaseLoader(),
      trim_blocks=True,           # Remove first newline after block tags
      lstrip_blocks=True,         # Strip leading whitespace from block tags  
      keep_trailing_newline=False # Remove trailing newlines
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
    self.vars, self.var_defaults = self._parse_template_variables(content)

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
  
  def _parse_template_variables(self, template_content: str) -> Tuple[Set[str], Dict[str, Any]]:
    """Parse Jinja2 template to extract variables and their default values.
    
    Examples:
        {{ app_name | default('my-app') }} → vars={'app_name'}, defaults={'app_name': 'my-app'}
        {{ port | default(8080) }} → vars={'port'}, defaults={'port': 8080}
        {{ unused_var }} → vars={'unused_var'}, defaults={}
    
    Returns:
        Tuple of (all_variable_names, variable_defaults)
    """
    try:
      env = self._create_jinja_env()
      ast = env.parse(template_content)
      
      # Extract all undeclared variables
      all_variables = meta.find_undeclared_variables(ast)
      
      # Extract default values from | default() filters
      defaults = {
        node.node.name: node.args[0].value
        for node in ast.find_all(nodes.Filter)
        if node.name == 'default' 
        and isinstance(node.node, nodes.Name) 
        and node.args 
        and isinstance(node.args[0], nodes.Const)
      }
      
      return all_variables, defaults
    except Exception:
      return set(), {}

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
      rendered_content = jinja_template.render(**variable_values)
      
      # Clean up excessive blank lines and whitespace
      rendered_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', rendered_content)
      return rendered_content.strip()
      
    except Exception as e:
      logger.error(f"Jinja2 template rendering failed: {e}")
      raise ValueError(f"Failed to render template: {e}")
