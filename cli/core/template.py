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
  relative_path: str = field(init=False)
  size: int = field(init=False)
  
  # Template variable analysis results
  vars: Dict[str, Any] = field(default_factory=dict, init=False)
  frontmatter_variables: Dict[str, Any] = field(default_factory=dict, init=False)
  
  # Cache for performance optimization
  _jinja_ast: Any = field(default=None, init=False, repr=False)
  _parsed_vars: Dict[str, Any] = field(default=None, init=False, repr=False)
  _is_enriched: bool = field(default=False, init=False, repr=False)
 
  def __post_init__(self):
    """Initialize computed properties after dataclass initialization."""
    # Set default name if not provided
    if not self.name:
      self.name = self.file_path.parent.name
    
    # Computed properties
    self.id = self.file_path.parent.name
    self.relative_path = self.file_path.name
    self.size = self.file_path.stat().st_size if self.file_path.exists() else 0
    
    # Initialize with empty vars - modules will enrich with their variables
    # Template parsing and variable enrichment is handled by the module
    self.vars = {}

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
      
      logger.info(f"Loaded template '{template.id}' (v{template.version or 'unversioned'}, {template.size} bytes)")
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

  def render(self, variable_values: Dict[str, Any]) -> str:
    """Render the template with the provided variable values."""
    logger = logging.getLogger('boilerplates')
    
    try:
      logger.debug(f"Rendering template '{self.id}' with {len(variable_values)} provided variables")
      env = self._create_jinja_env()
      jinja_template = env.from_string(self.content)
      # Merge template vars (with defaults) with provided values
      # All variables should be defined at this point due to validation
      merged_variable_values = {**self.vars, **variable_values}
      logger.debug(f"Final render context has {len(merged_variable_values)} variables")
      
      rendered_content = jinja_template.render(**merged_variable_values)
      initial_size = len(rendered_content)
      
      # Clean up excessive blank lines and whitespace
      rendered_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', rendered_content)
      final_content = rendered_content.strip()
      
      logger.info(f"Successfully rendered template '{self.id}' ({initial_size} -> {len(final_content)} bytes)")
      return final_content
      
    except Exception as e:
      logger.error(f"Failed to render template '{self.id}': {e}")
      raise ValueError(f"Failed to render template: {e}")

  def _parse_template_variables(self, template_content: str, frontmatter_vars: Dict[str, Any] = None) -> Dict[str, Any]:
    """Parse Jinja2 template to extract variables and their defaults (cached).
    
    Handles:
    - Simple variables: service_name
    - Dotted notation: traefik.host, service_port.http
    - Frontmatter variable definitions
    
    Args:
        template_content: The Jinja2 template content (ignored if cached)
        frontmatter_vars: Variables defined in template frontmatter
    
    Returns:
        Dict mapping variable names to their default values (None if no default)
    """
    # Use cache if available and no frontmatter changes
    cache_key = f"{hash(frontmatter_vars.__str__() if frontmatter_vars else 'None')}"
    if self._parsed_vars is not None and not frontmatter_vars:
      return self._parsed_vars
    
    try:
      ast = self._get_ast()  # Use cached AST
      
      # Get all variables used in template
      all_variables = self._get_used_variables()
      if all_variables:
        logger.debug(f"Template uses {len(all_variables)} variables: {sorted(all_variables)}")
      else:
        logger.debug("Template does not use any variables")
      
      # Initialize vars dict with all variables (default to None)
      vars_dict = {var_name: None for var_name in all_variables}
      
      # Extract default values from | default() filters
      template_defaults = {}
      for node in ast.find_all(nodes.Filter):
        if node.name == 'default' and node.args and isinstance(node.args[0], nodes.Const):
          # Handle simple variable defaults
          if isinstance(node.node, nodes.Name):
            template_defaults[node.node.name] = node.args[0].value
            vars_dict[node.node.name] = node.args[0].value
          # Handle dotted variable defaults
          elif isinstance(node.node, nodes.Getattr):
            dotted_name = Template._build_dotted_name(node.node)
            if dotted_name:
              template_defaults[dotted_name] = node.args[0].value
              vars_dict[dotted_name] = node.args[0].value
      
      if template_defaults:
        logger.info(f"Template defines {len(template_defaults)} variable defaults")
        logger.debug(f"Template default values: {template_defaults}")
      
      # Process frontmatter variables (frontmatter takes precedence)
      if frontmatter_vars:
        frontmatter_overrides = {}
        for var_name, var_config in frontmatter_vars.items():
          if var_name in vars_dict and vars_dict[var_name] is not None:
            logger.warning(f"Variable '{var_name}' defined in both template content and frontmatter. Frontmatter definition takes precedence.")
          
          # Handle both simple values and complex variable configurations
          if isinstance(var_config, dict) and 'default' in var_config:
            frontmatter_overrides[var_name] = var_config['default']
            vars_dict[var_name] = var_config['default']
          else:
            frontmatter_overrides[var_name] = var_config
            vars_dict[var_name] = var_config
        
        if frontmatter_overrides:
          logger.info(f"Frontmatter defines/overrides {len(frontmatter_overrides)} variables")
          logger.debug(f"Frontmatter variable values: {frontmatter_overrides}")
      
      # Cache result if no frontmatter (pure template parsing)
      if not frontmatter_vars:
        self._parsed_vars = vars_dict.copy()
      
      return vars_dict
    except Exception as e:
      logger.debug(f"Error parsing template variables: {e}")
      return {}
