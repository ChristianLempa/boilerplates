from __future__ import annotations

from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Library:
  """Represents a single library with a specific path."""
  
  def __init__(self, name: str, path: Path, priority: int = 0) -> None:
    """Initialize a library instance.
    
    Args:
      name: Display name for the library
      path: Path to the library directory
      priority: Priority for library lookup (higher = checked first)
    """
    self.name = name
    self.path = path
    self.priority = priority  # Higher priority = checked first
  
  def _is_template_draft(self, template_path: Path) -> bool:
    """Check if a template is marked as draft.
    
    Args:
        template_path: Path to the template directory
    
    Returns:
        True if the template is marked as draft, False otherwise
    """
    import yaml
    
    # Find the template file
    template_file = None
    if (template_path / "template.yaml").exists():
      template_file = template_path / "template.yaml"
    elif (template_path / "template.yml").exists():
      template_file = template_path / "template.yml"
    
    if not template_file:
      return False
    
    try:
      with open(template_file, "r", encoding="utf-8") as f:
        documents = list(yaml.safe_load_all(f))
        valid_docs = [doc for doc in documents if doc is not None]
        
        if not valid_docs:
          return False
        
        template_data = valid_docs[0]
        metadata = template_data.get("metadata", {})
        return metadata.get("draft", False)
    except Exception as e:
      logger.warning(f"Error checking draft status for {template_path}: {e}")
      return False

  def find_by_id(self, module_name: str, template_id: str) -> tuple[Path, str]:
    """Find a template by its ID in this library.
    
    Args:
        module_name: The module name (e.g., 'compose', 'terraform')
        template_id: The template ID to find
    
    Returns:
        Path to the template directory if found
        
    Raises:
        FileNotFoundError: If the template ID is not found in this library or is marked as draft
    """
    logger.debug(f"Looking for template '{template_id}' in module '{module_name}' in library '{self.name}'")
    
    # Build the path to the specific template directory
    template_path = self.path / module_name / template_id
    
    # Check if the template directory and either template.yaml or template.yml exist
    if not (template_path.is_dir() and ((template_path / "template.yaml").exists() or (template_path / "template.yml").exists())):
      raise FileNotFoundError(f"Template '{template_id}' not found in module '{module_name}' in library '{self.name}'")
    
    # Check if template is marked as draft
    if self._is_template_draft(template_path):
      raise FileNotFoundError(f"Template '{template_id}' is marked as draft and cannot be used")
    
    logger.debug(f"Found template '{template_id}' at: {template_path}")
    return template_path, self.name


  def find(self, module_name: str, sort_results: bool = False) -> list[tuple[Path, str]]:
    """Find templates in this library for a specific module.
    
    Excludes templates marked as draft.
    
    Args:
        module_name: The module name (e.g., 'compose', 'terraform')
        sort_results: Whether to return results sorted alphabetically
    
    Returns:
        List of Path objects representing template directories (excluding drafts)
        
    Raises:
        FileNotFoundError: If the module directory is not found in this library
    """
    logger.debug(f"Looking for templates in module '{module_name}' in library '{self.name}'")
    
    # Build the path to the module directory
    module_path = self.path / module_name
    
    # Check if the module directory exists
    if not module_path.is_dir():
      raise FileNotFoundError(f"Module '{module_name}' not found in library '{self.name}'")
    
    # Get all directories in the module path that contain a template.yaml or template.yml file
    # and are not marked as draft
    template_dirs = []
    try:
      for item in module_path.iterdir():
        if item.is_dir() and ((item / "template.yaml").exists() or (item / "template.yml").exists()):
          # Skip draft templates
          if not self._is_template_draft(item):
            template_dirs.append((item, self.name))
          else:
            logger.debug(f"Skipping draft template: {item.name}")
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
  def __init__(self) -> None:

    # get the root path of the repository
    repo_root = Path(__file__).parent.parent.parent.resolve()

    self.libraries = [
      Library(name="default", path=repo_root / "library", priority=0)
    ]

  def find_by_id(self, module_name: str, template_id: str) -> Optional[tuple[Path, str]]:
    """Find a template by its ID across all libraries.
    
    Args:
        module_name: The module name (e.g., 'compose', 'terraform')
        template_id: The template ID to find
    
    Returns:
        Path to the template directory if found, None otherwise
    """
    logger.debug(f"Searching for template '{template_id}' in module '{module_name}' across all libraries")
    
    for library in sorted(self.libraries, key=lambda x: x.priority, reverse=True):
      try:
        template_path, lib_name = library.find_by_id(module_name, template_id)
        logger.debug(f"Found template '{template_id}' in library '{library.name}'")
        return template_path, lib_name
      except FileNotFoundError:
        # Continue searching in next library
        continue
    
    logger.debug(f"Template '{template_id}' not found in any library")
    return None
  
  def find(self, module_name: str, sort_results: bool = False) -> list[tuple[Path, str]]:
    """Find templates across all libraries for a specific module.
    
    Args:
        module_name: The module name (e.g., 'compose', 'terraform')
        sort_results: Whether to return results sorted alphabetically
    
    Returns:
        List of Path objects representing template directories from all libraries
    """
    logger.debug(f"Searching for templates in module '{module_name}' across all libraries")
    
    all_templates = []
    
    for library in sorted(self.libraries, key=lambda x: x.priority, reverse=True):
      try:
        templates = library.find(module_name, sort_results=False)  # Sort at the end
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
