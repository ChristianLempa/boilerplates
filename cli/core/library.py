from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from .template import Template


class Library:
  """Represents a single library with a specific path."""
  
  def __init__(self, name: str, path: Path):
    self.name = name
    self.path = path

  def find_by_id(self, module_name: str, files: list[str], template_id: str) -> "Template | None":
    """Find a template by its ID in this library."""
    for template in self.find(module_name, files, sorted=False):
      if template.id == template_id:
        return template
    return None

  def find(self, module_name: str, files: list[str], sorted: bool = False) -> list["Template"]:
    """Find templates in this library for a specific module."""
    from .template import Template  # Import here to avoid circular import
    
    templates = []
    module_path = self.path / module_name
    
    if not module_path.exists():
      return templates
    
    # Find all files matching the specified filenames
    for filename in files:
      for file_path in module_path.rglob(filename):
        if file_path.is_file():
          # Create Template object using the new class method
          template = Template.from_file(file_path)
          templates.append(template)

    if sorted:
      templates.sort(key=lambda t: t.id)

    return templates


class LibraryManager:
  """Manager for multiple libraries."""
  
  def __init__(self):
    self.libraries = []
    # Initialize with the default library
    script_dir = Path(__file__).parent.parent.parent  # Go up from cli/core/ to project root
    default_library = Library("default", script_dir / "library")
    self.libraries.append(default_library)
  
  def add_library(self, library: Library):
    """Add a library to the collection."""
    self.libraries.append(library)

  def find(self, module_name: str, files: list[str], sorted: bool = False) -> list["Template"]:
    """Find templates across all libraries for a specific module."""
    all_templates = []
    
    for library in self.libraries:
      templates = library.find(module_name, files, sorted=sorted)
      all_templates.extend(templates)

    if sorted:
      all_templates.sort(key=lambda t: t.id)

    return all_templates

  def find_by_id(self, module_name: str, files: list[str], template_id: str) -> "Template | None":
    """Find a template by its ID across all libraries."""
    for library in self.libraries:
      template = library.find_by_id(module_name, files, template_id)
      if template:
        return template
    return None
