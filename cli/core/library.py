from pathlib import Path
import logging
logger = logging.getLogger(__name__)


class Library:
  """Represents a single library with a specific path."""
  
  def __init__(self, name: str, path: Path, priority: int = 0):
    self.name = name
    self.path = path
    self.priority = priority  # Higher priority = checked first

  def find_by_id(self, module_name, files, template_id):
    """Find a template by its ID in this library.
    
    Args:
        module_name: The module name (e.g., 'compose', 'terraform')
        files: List of files to look for in the template directory
        template_id: The template ID to find
    
    Returns:
        Path to the template directory if found
        
    Raises:
        FileNotFoundError: If the template ID is not found in this library
    """
    logger.debug(f"Looking for template '{template_id}' in module '{module_name}' in library '{self.name}'")
    
    # Build the path to the specific template directory
    template_path = self.path / module_name / template_id
    
    # Check if the template directory exists
    if not template_path.exists():
      raise FileNotFoundError(f"Template '{template_id}' not found in module '{module_name}' in library '{self.name}'")
    
    if not template_path.is_dir():
      raise FileNotFoundError(f"Template '{template_id}' exists but is not a directory in module '{module_name}' in library '{self.name}'")
    
    # If files list is provided, verify at least one of the files exists
    if files:
      has_any_file = False
      for file in files:
        file_path = template_path / file
        if file_path.exists():
          has_any_file = True
          break
      
      if not has_any_file:
        raise FileNotFoundError(f"Template '{template_id}' found but missing any of the required files: {files}")
    
    logger.debug(f"Found template '{template_id}' at: {template_path}")
    return template_path, self.name


  def find(self, module_name, files, sort_results=False):
    """Find templates in this library for a specific module.
    
    Args:
        module_name: The module name (e.g., 'compose', 'terraform')
        files: List of files to look for in template directories (optional filter)
        sort_results: Whether to return results sorted alphabetically
    
    Returns:
        List of Path objects representing template directories
        
    Raises:
        FileNotFoundError: If the module directory is not found in this library
    """
    logger.debug(f"Looking for templates in module '{module_name}' in library '{self.name}'")
    
    # Build the path to the module directory
    module_path = self.path / module_name
    
    # Check if the module directory exists
    if not module_path.exists():
      raise FileNotFoundError(f"Module '{module_name}' not found in library '{self.name}'")
    
    if not module_path.is_dir():
      raise FileNotFoundError(f"Module '{module_name}' exists but is not a directory in library '{self.name}'")
    
    # Get all directories in the module path
    template_dirs = []
    try:
      for item in module_path.iterdir():
        if item.is_dir():
          # If files list is provided, check if template has any of the required files
          if files:
            has_any_file = False
            for file in files:
              file_path = item / file
              if file_path.exists():
                has_any_file = True
                break

            if has_any_file:
              template_dirs.append((item, self.name))
          else:
            # No file requirements, include all directories
            template_dirs.append((item, self.name))
    except PermissionError as e:
      raise FileNotFoundError(f"Permission denied accessing module '{module_name}' in library '{self.name}': {e}")
    
    # Sort if requested
    if sort_results:
      template_dirs.sort(key=lambda x: x[0].name.lower())
    
    logger.debug(f"Found {len(template_dirs)} templates in module '{module_name}'")
    return template_dirs


class LibraryManager:
  """Manages multiple libraries and provides methods to find templates."""
  
  # FIXME: For now this is static and only has one library
  def __init__(self):

    # get the root path of the repository
    repo_root = Path(__file__).parent.parent.parent.resolve()

    self.libraries = [
      Library(name="default", path=repo_root / "library", priority=0)
    ]

  def find_by_id(self, module_name, files, template_id):
    """Find a template by its ID across all libraries.
    
    Args:
        module_name: The module name (e.g., 'compose', 'terraform')
        files: List of files to look for in the template directory
        template_id: The template ID to find
    
    Returns:
        Path to the template directory if found, None otherwise
    """
    logger.debug(f"Searching for template '{template_id}' in module '{module_name}' across all libraries")
    
    for library in sorted(self.libraries, key=lambda x: x.priority, reverse=True):
      try:
        template_path, lib_name = library.find_by_id(module_name, files, template_id)
        logger.debug(f"Found template '{template_id}' in library '{library.name}'")
        return template_path, lib_name
      except FileNotFoundError:
        # Continue searching in next library
        continue
    
    logger.debug(f"Template '{template_id}' not found in any library")
    return None
  
  def find(self, module_name, files, sort_results=False):
    """Find templates across all libraries for a specific module.
    
    Args:
        module_name: The module name (e.g., 'compose', 'terraform')
        files: List of files to look for in template directories (optional filter)
        sort_results: Whether to return results sorted alphabetically
    
    Returns:
        List of Path objects representing template directories from all libraries
    """
    logger.debug(f"Searching for templates in module '{module_name}' across all libraries")
    
    all_templates = []
    
    for library in sorted(self.libraries, key=lambda x: x.priority, reverse=True):
      try:
        templates = library.find(module_name, files, sort_results=False)  # Sort at the end
        all_templates.extend(templates)
        logger.debug(f"Found {len(templates)} templates in library '{library.name}'")
      except FileNotFoundError:
        # Module not found in this library, continue with next
        logger.debug(f"Module '{module_name}' not found in library '{library.name}'")
        continue
    
    # Remove duplicates based on template name (directory name)
    seen_names = set()
    unique_templates = []
    for template in all_templates:
      name, library_name = template
      if name.name not in seen_names:
        unique_templates.append((name, library_name))
        seen_names.add(name.name)
    
    # Sort if requested
    if sort_results:
      unique_templates.sort(key=lambda x: x[0].name.lower())
    
    logger.debug(f"Found {len(unique_templates)} unique templates total")
    return unique_templates
  
