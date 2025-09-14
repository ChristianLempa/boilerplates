from pathlib import Path
import subprocess
import logging
from .config import get_config, LibraryConfig
# Using standard Python exceptions

logger = logging.getLogger(__name__)


class Library:
  """Represents a single library with a specific path."""
  
  def __init__(self, name: str, path: Path, priority: int = 0):
    self.name = name
    self.path = path
    self.priority = priority  # Higher priority = checked first

  def find_by_id(self, module_name, files, template_id):
    """
    Find a template by its ID in this library.
    
    Args:
        module_name: The module name (e.g., 'terraform', 'compose') to search within.
                    This narrows the search to the specific technology directory in the library.
        files: List of file patterns to search for (e.g., ['*.tf', '*.yaml']).
               This filters templates to only those with matching file extensions,
               ensuring we only process relevant template files for the module.
        template_id: The unique identifier of the template to find.
                    This is typically derived from the template's directory name or filename.
    
    Returns:
        Template object if found, None otherwise.
    """
    from .template import Template  # Import here to avoid circular import
    
    logger.debug(f"Searching for template '{template_id}' in library '{self.name}' at {self.path} (module: {module_name})")
    
    module_path = self.path / module_name
    if not module_path.exists():
      logger.debug(f"Module path '{module_path}' does not exist in library '{self.name}'")
      return None
    
    # Try to find the template directory directly by ID
    template_dir = module_path / template_id
    if template_dir.exists() and template_dir.is_dir():
      # Look for template files in this specific directory
      for filename in files:
        for file_path in template_dir.glob(filename):
          if file_path.is_file():
            template = Template.from_file(file_path)
            # Set module context if not already specified in frontmatter
            if not template.module:
              template.module = module_name
            # Verify this is actually the template we want
            if template.id == template_id:
              logger.info(f"Found template '{template_id}' in library '{self.name}' (direct lookup)")
              return template
    
    # Fallback to the original method if direct lookup fails
    # This handles cases where template ID doesn't match directory structure
    logger.debug(f"Direct lookup failed for '{template_id}', falling back to full scan in library '{self.name}'")
    for template in self.find(module_name, files, sorted=False):
      if template.id == template_id:
        logger.info(f"Found template '{template_id}' in library '{self.name}' (full scan)")
        return template
    
    logger.debug(f"Template '{template_id}' not found in library '{self.name}'")
    return None

  def find(self, module_name, files, sorted=False):
    """Find templates in this library for a specific module."""
    from .template import Template  # Import here to avoid circular import
    
    logger.debug(f"Scanning for templates in library '{self.name}' (module: {module_name}, files: {files})")
    
    templates = []
    module_path = self.path / module_name
    
    if not module_path.exists():
      logger.debug(f"Module path '{module_path}' does not exist in library '{self.name}'")
      return templates
    
    # Find all files matching the specified filenames
    for filename in files:
      for file_path in module_path.rglob(filename):
        if file_path.is_file():
          # Create Template object using the new class method
          template = Template.from_file(file_path)
          # Set module context if not already specified in frontmatter
          if not template.module:
            template.module = module_name
          templates.append(template)

    if sorted:
      templates.sort(key=lambda t: t.id)

    if templates:
      logger.info(f"Found {len(templates)} templates in library '{self.name}' for module '{module_name}'")
    else:
      logger.debug(f"No templates found in library '{self.name}' for module '{module_name}'")
    return templates


class RemoteLibrary(Library):
  """Support for Git-based remote template libraries."""
  
  def __init__(self, name: str, repo_url: str, branch: str = "main", priority: int = 0):
    """Initialize a remote library.
    
    Args:
        name: Name of the library
        repo_url: Git repository URL
        branch: Branch to use (default: main)
        priority: Library priority (higher = checked first)
    """
    self.repo_url = repo_url
    self.branch = branch
    
    # Set up local cache path
    config = get_config()
    local_cache = config.cache_dir / name
    
    # Initialize parent with cache path
    super().__init__(name, local_cache, priority)
    
    # Update the cache on initialization if configured
    if config.auto_update_remotes:
      try:
        self.update()
      except Exception as e:
        logger.warning(f"Failed to auto-update remote library '{name}': {e}")
  
  def update(self) -> bool:
    """Pull latest changes from remote repository.
    
    Returns:
        True if update was successful, False otherwise
    """
    try:
      if not self.path.exists():
        # Clone repository
        logger.info(f"Cloning remote library '{self.name}' from {self.repo_url}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        result = subprocess.run(
          ["git", "clone", "-b", self.branch, self.repo_url, str(self.path)],
          capture_output=True,
          text=True,
          check=True
        )
        
        if result.returncode != 0:
          raise ConnectionError(f"Git clone failed for '{self.name}': {result.stderr}")
        
        logger.info(f"Successfully cloned library '{self.name}'")
        return True
        
      else:
        # Pull updates
        logger.info(f"Updating remote library '{self.name}'")
        
        # First, fetch to see if there are updates
        result = subprocess.run(
          ["git", "fetch", "origin", self.branch],
          cwd=self.path,
          capture_output=True,
          text=True
        )
        
        if result.returncode != 0:
          logger.warning(f"Failed to fetch updates for '{self.name}': {result.stderr}")
          return False
        
        # Check if we're behind
        result = subprocess.run(
          ["git", "rev-list", "--count", f"HEAD..origin/{self.branch}"],
          cwd=self.path,
          capture_output=True,
          text=True
        )
        
        behind_count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        
        if behind_count > 0:
          # Pull the updates
          result = subprocess.run(
            ["git", "pull", "origin", self.branch],
            cwd=self.path,
            capture_output=True,
            text=True,
            check=True
          )
          
          if result.returncode != 0:
            raise ConnectionError(f"Git pull failed for '{self.name}': {result.stderr}")
          
          logger.info(f"Successfully updated library '{self.name}' ({behind_count} new commits)")
          return True
        else:
          logger.debug(f"Library '{self.name}' is already up to date")
          return True
          
    except subprocess.CalledProcessError as e:
      raise RuntimeError(
        f"Git command failed for '{self.name}': {e.stderr if hasattr(e, 'stderr') else str(e)}"
      )
    except Exception as e:
      raise RuntimeError(f"Library update failed for '{self.name}': {str(e)}")
  
  def get_info(self) -> dict:
    """Get information about the remote library.
    
    Returns:
        Dictionary with library information
    """
    info = {
      'name': self.name,
      'type': 'remote',
      'repo': self.repo_url,
      'branch': self.branch,
      'priority': self.priority,
      'cached': self.path.exists(),
      'cache_path': str(self.path)
    }
    
    if self.path.exists():
      try:
        # Get current commit hash
        result = subprocess.run(
          ["git", "rev-parse", "HEAD"],
          cwd=self.path,
          capture_output=True,
          text=True
        )
        if result.returncode == 0:
          info['current_commit'] = result.stdout.strip()[:8]
        
        # Get last update time
        result = subprocess.run(
          ["git", "log", "-1", "--format=%ci"],
          cwd=self.path,
          capture_output=True,
          text=True
        )
        if result.returncode == 0:
          info['last_updated'] = result.stdout.strip()
          
      except Exception as e:
        logger.debug(f"Failed to get git info for '{self.name}': {e}")
    
    return info


class LibraryManager:
  """Manager for multiple libraries with priority-based ordering."""
  
  def __init__(self):
    self.libraries = []
    self._initialize_libraries()
  
  def _initialize_libraries(self):
    """Initialize libraries from configuration."""
    config = get_config()
    logger.info(f"Initializing library manager with {len(config.libraries)} configured libraries")
    
    # First, add configured libraries
    for lib_config in config.libraries:
      try:
        library = self._create_library_from_config(lib_config)
        if library:
          self.libraries.append(library)
          logger.info(f"Loaded library '{lib_config.name}' (type: {lib_config.type}, priority: {lib_config.priority})")
      except Exception as e:
        logger.warning(f"Failed to load library '{lib_config.name}': {e}")
    
    # Then add the default built-in library if not already configured
    if not any(lib.name == "default" for lib in self.libraries):
      script_dir = Path(__file__).parent.parent.parent  # Go up from cli/core/ to project root
      default_library = Library("default", script_dir / "library", priority=-1)  # Lower priority
      self.libraries.append(default_library)
      logger.info(f"Added default built-in library at '{script_dir / 'library'}' (priority: -1)")
    
    # Sort libraries by priority (highest first)
    self._sort_by_priority()
    logger.info(f"Successfully initialized {len(self.libraries)} libraries")
    if self.libraries:
      logger.debug(f"Libraries in priority order: {[(lib.name, lib.priority) for lib in self.libraries]}")
  
  def _create_library_from_config(self, lib_config):
    """Create a Library instance from configuration.
    
    Args:
        lib_config: LibraryConfig instance
        
    Returns:
        Library instance or None if creation fails
    """
    if lib_config.type == "local":
      if lib_config.path:
        path = Path(lib_config.path).expanduser()
        if path.exists():
          return Library(lib_config.name, path, lib_config.priority)
        else:
          logger.warning(f"Local library path does not exist: {path}")
          return None
    elif lib_config.type == "git":
      if lib_config.repo:
        return RemoteLibrary(
          lib_config.name,
          lib_config.repo,
          lib_config.branch,
          lib_config.priority
        )
      else:
        logger.warning(f"Git library '{lib_config.name}' missing repo URL")
        return None
    else:
      logger.warning(f"Unknown library type: {lib_config.type}")
      return None
  
  def _sort_by_priority(self):
    """Sort libraries by priority (highest first)."""
    self.libraries.sort(key=lambda lib: lib.priority, reverse=True)
  
  def add_library(self, library: Library):
    """Add a library to the collection.
    
    Args:
        library: Library instance to add
    """
    # Check for duplicate names
    if any(lib.name == library.name for lib in self.libraries):
      logger.warning(f"Library '{library.name}' already exists, replacing")
      self.libraries = [lib for lib in self.libraries if lib.name != library.name]
    
    self.libraries.append(library)
    self._sort_by_priority()

  def find(self, module_name, files, sorted=False):
    """Find templates across all libraries for a specific module."""
    logger.debug(f"Searching across {len(self.libraries)} libraries for module '{module_name}'")
    all_templates = []
    library_counts = {}
    
    for library in self.libraries:
      templates = library.find(module_name, files, sorted=sorted)
      if templates:
        library_counts[library.name] = len(templates)
      all_templates.extend(templates)

    if sorted:
      all_templates.sort(key=lambda t: t.id)

    if all_templates:
      logger.info(f"Found {len(all_templates)} total templates for module '{module_name}'")
      if library_counts:
        logger.debug(f"Template distribution: {library_counts}")
    else:
      logger.debug(f"No templates found for module '{module_name}' across any library")
    return all_templates

  def find_by_id(self, module_name, files, template_id):
    """
    Find a template by its ID across all libraries.
    
    Args:
        module_name: The module name (e.g., 'terraform', 'compose') to search within.
                    This narrows the search to the specific technology directory across all libraries,
                    allowing for modular organization of templates by technology type.
        files: List of file patterns to search for (e.g., ['*.tf', '*.yaml']).
               This filters templates to only those with matching file extensions,
               ensuring we only process relevant template files for the specific module type.
        template_id: The unique identifier of the template to find.
                    This is typically derived from the template's directory name or filename,
                    providing a human-readable way to reference specific templates.
    
    Returns:
        Template object if found across any library, None otherwise.
        
    Note:
        This method searches through all registered libraries in priority order (highest first),
        returning the first matching template found. This allows higher-priority libraries
        to override templates from lower-priority ones.
    """
    logger.debug(f"Searching for template '{template_id}' across {len(self.libraries)} libraries (module: {module_name})")
    for library in self.libraries:  # Already sorted by priority
      template = library.find_by_id(module_name, files, template_id)
      if template:
        logger.info(f"Retrieved template '{template_id}' from library '{library.name}' (priority: {library.priority})")
        return template
    
    logger.warning(f"Template '{template_id}' not found in any library")
    return None
