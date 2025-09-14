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
  """Data class for template information extracted from frontmatter."""
  
  # Required fields
  file_path: Path
  content: str = ""
  
  # Frontmatter fields with defaults
  id: str = ""
  name: str = ""
  description: str = "No description available"
  author: str = ""
  date: str = ""
  version: str = ""
  module: str = ""
  tags: List[str] = field(default_factory=list)
  files: List[str] = field(default_factory=list)
  
  # Template variable analysis results
  vars: Dict[str, Any] = field(default_factory=dict, init=False)



  @classmethod
  def from_file(cls, file_path: Path) -> "Template":
    """Create a Template instance from a file path.
    
    Args:
        file_path: Path to the template file
    """
    logger.debug(f"Loading template from file: {file_path}")
    try:
      frontmatter_data, content = cls._parse_frontmatter(file_path)
      template = cls(
        file_path=file_path,
        content=content,
        name=frontmatter_data.get('name', ''),
        description=frontmatter_data.get('description', 'No description available'),
        author=frontmatter_data.get('author', ''),
        date=frontmatter_data.get('date', ''),
        version=frontmatter_data.get('version', ''),
        module=frontmatter_data.get('module', ''),
        tags=frontmatter_data.get('tags', []),
        files=frontmatter_data.get('files', [])
      )
      # Store frontmatter variables - module enrichment will handle the integration
      template.frontmatter_variables = frontmatter_data.get('variables', {})
      
      if template.frontmatter_variables:
        logger.debug(f"Template '{template.id}' has {len(template.frontmatter_variables)} frontmatter variables: {list(template.frontmatter_variables.keys())}")
      
      logger.info(f"Loaded template '{template.id}' (v{template.version or 'unversioned'}")
      logger.debug(f"Template details: author='{template.author}', tags={template.tags}")
      return template
    except Exception as e:
      # If frontmatter parsing fails, create a basic Template object
      logger.warning(f"Failed to parse frontmatter for {file_path}: {e}. Creating basic template.")
      return cls(file_path=file_path)
  
  @staticmethod
  def _build_dotted_name(node) -> Optional[str]:
    """Build full dotted variable name from Jinja2 Getattr node.
    
    Returns:
        Dotted variable name (e.g., 'traefik.host') or None if invalid
    """
    current = node
    parts = []
    while isinstance(current, nodes.Getattr):
      parts.insert(0, current.attr)
      current = current.node
    if isinstance(current, nodes.Name):
      parts.insert(0, current.name)
      return '.'.join(parts)
    return None

  @staticmethod
  def _create_jinja_env() -> Environment:
    """Create standardized Jinja2 environment for consistent template processing."""
    return Environment(
      loader=BaseLoader(),
      trim_blocks=True,  # Remove first newline after block tags
      lstrip_blocks=True,  # Strip leading whitespace from block tags
      keep_trailing_newline=False  # Remove trailing newlines
    )
  
  def _get_ast(self):
    """Get cached AST or create and cache it."""
    if self._jinja_ast is None:
      env = self._create_jinja_env()
      self._jinja_ast = env.parse(self.content)
    return self._jinja_ast
  
  def _get_used_variables(self) -> Set[str]:
    """Get variables actually used in template (cached)."""
    ast = self._get_ast()
    used_variables = meta.find_undeclared_variables(ast)
    initial_count = len(used_variables)
    
    # Handle dotted notation variables
    dotted_vars = []
    for node in ast.find_all(nodes.Getattr):
      dotted_name = Template._build_dotted_name(node)
      if dotted_name:
        used_variables.add(dotted_name)
        dotted_vars.append(dotted_name)
    
    if dotted_vars:
      logger.debug(f"Found {len(dotted_vars)} dotted variables in addition to {initial_count} simple variables")
    
    return used_variables
  
  @staticmethod
  def _parse_frontmatter(file_path: Path) -> Tuple[Dict[str, Any], str]:
    """Parse frontmatter and content from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
      post = frontmatter.load(f)
    return post.metadata, post.content
