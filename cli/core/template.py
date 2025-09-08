from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
from dataclasses import dataclass, field
import logging
import re
from jinja2 import Environment, BaseLoader, meta, nodes, TemplateSyntaxError
import frontmatter
from .exceptions import TemplateValidationError
from .variables import TemplateVariable, analyze_template_variables


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
  
  # Computed properties (will be set in __post_init__)
  id: str = field(init=False)
  directory: str = field(init=False)
  relative_path: str = field(init=False)
  size: int = field(init=False)
  
  # Template variable analysis results
  vars: Set[str] = field(default_factory=set, init=False)
  var_defaults: Dict[str, Any] = field(default_factory=dict, init=False)
  var_dict_keys: Dict[str, List[str]] = field(default_factory=dict, init=False)  # Track dict access patterns
  variables: Dict[str, TemplateVariable] = field(default_factory=dict, init=False)  # Analyzed variables
  
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
    self.vars, self.var_defaults, self.var_dict_keys = self._parse_template_variables(self.content)
    # Analyze variables to create TemplateVariable objects
    self.variables = analyze_template_variables(
      self.vars, self.var_defaults, self.var_dict_keys, self.content
    )
  
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
        files=frontmatter_data.get('files', [])
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
  
  def _parse_template_variables(self, template_content: str) -> Tuple[Set[str], Dict[str, Any], Dict[str, List[str]]]:
    """Parse Jinja2 template to extract variables and their defaults.
    
    Handles multiple patterns:
    - Simple variables: service_name
    - Dotted notation: traefik.host
    - Dict notation: service_port['http']
    - Nested patterns: nginx_dashboard.port['dashboard']
    
    Returns:
        Tuple of (all_variable_names, variable_defaults, dict_access_patterns)
    """
    try:
      env = self._create_jinja_env()
      ast = env.parse(template_content)
      
      # Start with variables found by Jinja2's meta utility
      all_variables = meta.find_undeclared_variables(ast)
      
      # Track dict access patterns
      dict_keys = {}  # var_name -> list of keys accessed
      
      # Handle all Getitem nodes (dict access)
      for node in ast.find_all(nodes.Getitem):
        if isinstance(node.arg, nodes.Const) and isinstance(node.arg.value, str):
          key = node.arg.value
          current = node.node
          
          # Handle nested patterns like nginx_dashboard.port['dashboard']
          if isinstance(current, nodes.Getattr):
            # Build the full dotted name
            parts = [current.attr]
            base = current.node
            while isinstance(base, nodes.Getattr):
              parts.insert(0, base.attr)
              base = base.node
            if isinstance(base, nodes.Name):
              parts.insert(0, base.name)
              var_name = '.'.join(parts)
              # This is a dotted variable with dict access
              all_variables.add(var_name)
              if var_name not in dict_keys:
                dict_keys[var_name] = []
              if key not in dict_keys[var_name]:
                dict_keys[var_name].append(key)
          
          # Handle simple dict access like service_port['http']
          elif isinstance(current, nodes.Name):
            var_name = current.name
            if var_name not in dict_keys:
              dict_keys[var_name] = []
            if key not in dict_keys[var_name]:
              dict_keys[var_name].append(key)
      
      # Handle dotted notation variables (like traefik.host, swarm.replicas)
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
          
          # Handle dict access defaults
          elif isinstance(node.node, nodes.Getitem):
            if isinstance(node.node.arg, nodes.Const):
              key = node.node.arg.value
              
              # Handle nested pattern defaults: {{ nginx_dashboard.port['dashboard'] | default(8081) }}
              if isinstance(node.node.node, nodes.Getattr):
                # Build the full dotted name
                parts = []
                current = node.node.node
                while isinstance(current, nodes.Getattr):
                  parts.insert(0, current.attr)
                  current = current.node
                if isinstance(current, nodes.Name):
                  parts.insert(0, current.name)
                  var_name = '.'.join(parts)
                  if var_name not in defaults:
                    defaults[var_name] = {}
                  if not isinstance(defaults[var_name], dict):
                    defaults[var_name] = {}
                  defaults[var_name][key] = node.args[0].value
              
              # Handle simple dict defaults: {{ var['key'] | default(value) }}
              elif isinstance(node.node.node, nodes.Name):
                var_name = node.node.node.name
                if var_name not in defaults:
                  defaults[var_name] = {}
                if not isinstance(defaults[var_name], dict):
                  defaults[var_name] = {}
                defaults[var_name][key] = node.args[0].value
          
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
      
      return all_variables, defaults, dict_keys
    except Exception as e:
      logging.getLogger('boilerplates').debug(f"Error parsing template variables: {e}")
      return set(), {}, {}

  def validate(self) -> List[str]:
    """Validate template integrity.
    
    Returns:
        List of validation error messages. Empty list if valid.
    
    Raises:
        TemplateValidationError: If validation fails (critical errors only).
    """
    errors = []
    
    # Check for Jinja2 syntax errors (critical - should raise immediately)
    try:
      env = self._create_jinja_env()
      env.from_string(self.content)
    except TemplateSyntaxError as e:
      raise TemplateValidationError(self.id, [f"Invalid Jinja2 syntax at line {e.lineno}: {e.message}"])
    except Exception as e:
      raise TemplateValidationError(self.id, [f"Template parsing error: {str(e)}"])
    
    # All variables are now auto-detected, no need to check for undefined
    # The template parser will have found all variables used
    
    # Check for missing required frontmatter fields
    if not self.name or self.name == self.file_path.parent.name:
      errors.append("Missing 'name' in frontmatter")
    
    if not self.description or self.description == 'No description available':
      errors.append("Missing 'description' in frontmatter")
    
    # Check for empty content (unless it's intentionally a metadata-only template)
    if not self.content.strip() and not self.files:
      errors.append("Template has no content")
    
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
