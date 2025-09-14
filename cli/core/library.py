from pathlib import Path
import subprocess
import logging

logger = logging.getLogger(__name__)


class Library:
  """Represents a single library with a specific path."""
  
  def __init__(self, name: str, path: Path, priority: int = 0):
    self.name = name
    self.path = path
    self.priority = priority  # Higher priority = checked first

  def find_by_id(self, module_name, files, template_id):
    """Find a template by its ID in this library."""
    pass

  def find(self, module_name, files, sorted=False):
    """Find templates in this library for a specific module."""
    pass

class LibraryManager:
  """Manages multiple libraries and provides methods to find templates."""
  
  # FIXME: For now this is static and only has one library
  def __init__(self):
    self.libraries = [
      Library(name="default", path=Path(__file__).parent.parent / "libraries", priority=0)
    ]

  def find_by_id(self, module_name, files, template_id):
    """Find a template by its ID across all libraries."""
    for library in self.libraries:
      template = library.find_by_id(module_name, files, template_id)
      if template:
        return template
  
  def find(self, module_name, files, sorted=False):
    """Find templates across all libraries for a specific module."""
    for library in self.libraries:
      templates = library.find(module_name, files, sorted=sorted)
      if templates:
        return templates
    return []
