from __future__ import annotations

from pathlib import Path
import logging
from typing import Optional
import yaml

from .exceptions import LibraryError, TemplateNotFoundError, YAMLParseError

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
    """Check if a template is marked as draft."""
    # Find the template file
    for filename in ("template.yaml", "template.yml"):
      template_file = template_path / filename
      if template_file.exists():
        break
    else:
      return False
    
    try:
      with open(template_file, "r", encoding="utf-8") as f:
        docs = [doc for doc in yaml.safe_load_all(f) if doc]
        return docs[0].get("metadata", {}).get("draft", False) if docs else False
    except (yaml.YAMLError, IOError, OSError) as e:
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
    
    # Check if template directory exists with a template file
    has_template = template_path.is_dir() and any(
      (template_path / f).exists() for f in ("template.yaml", "template.yml")
    )
    
    if not has_template or self._is_template_draft(template_path):
      raise TemplateNotFoundError(template_id, module_name)
    
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
      raise LibraryError(f"Module '{module_name}' not found in library '{self.name}'")
    
    # Get non-draft templates
    template_dirs = []
    try:
      for item in module_path.iterdir():
        has_template = item.is_dir() and any((item / f).exists() for f in ("template.yaml", "template.yml"))
        if has_template and not self._is_template_draft(item):
          template_dirs.append((item, self.name))
        elif has_template:
          logger.debug(f"Skipping draft template: {item.name}")
    except PermissionError as e:
      raise LibraryError(f"Permission denied accessing module '{module_name}' in library '{self.name}': {e}")
    
    # Sort if requested
    if sort_results:
      template_dirs.sort(key=lambda x: x[0].name.lower())
    
    logger.debug(f"Found {len(template_dirs)} templates in module '{module_name}'")
    return template_dirs

class LibraryManager:
  """Manages multiple libraries and provides methods to find templates."""
  
  def __init__(self) -> None:
    """Initialize LibraryManager with git-based libraries from config."""
    from .config import ConfigManager
    
    self.config = ConfigManager()
    self.libraries = self._load_libraries_from_config()
  
  def _load_libraries_from_config(self) -> list[Library]:
    """Load libraries from configuration.
    
    Returns:
        List of Library instances
    """
    libraries = []
    libraries_path = self.config.get_libraries_path()
    
    # Get library configurations from config
    library_configs = self.config.get_libraries()
    
    for i, lib_config in enumerate(library_configs):
      # Skip disabled libraries
      if not lib_config.get("enabled", True):
        logger.debug(f"Skipping disabled library: {lib_config.get('name')}")
        continue
      
      name = lib_config.get("name")
      directory = lib_config.get("directory", ".")
      
      # Build path to library: ~/.config/boilerplates/libraries/{name}/{directory}/
      # For sparse-checkout, files remain in the specified directory
      library_base = libraries_path / name
      if directory and directory != ".":
        library_path = library_base / directory
      else:
        library_path = library_base
      
      # Check if library path exists
      if not library_path.exists():
        logger.warning(
          f"Library '{name}' not found at {library_path}. "
          f"Run 'repo update' to sync libraries."
        )
        continue
      
      # Create Library instance with priority based on order (first = highest priority)
      priority = len(library_configs) - i
      libraries.append(Library(name=name, path=library_path, priority=priority))
      logger.debug(f"Loaded library '{name}' from {library_path} with priority {priority}")
    
    if not libraries:
      logger.warning("No libraries loaded. Run 'repo update' to sync libraries.")
    
    return libraries

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
      except TemplateNotFoundError:
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
      except LibraryError:
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
