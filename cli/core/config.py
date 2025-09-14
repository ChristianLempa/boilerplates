"""Global configuration management for the boilerplate CLI."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging
import yaml

# Using standard Python exceptions

logger = logging.getLogger('boilerplates')


@dataclass
class LibraryConfig:
  """Configuration for a single library."""
  name: str
  type: str  # 'local' or 'git'
  path: Optional[str] = None  # For local libraries
  repo: Optional[str] = None  # For git libraries
  branch: str = "main"  # For git libraries
  priority: int = 0  # Higher priority = checked first


@dataclass
class Config:
  """Global configuration management."""
  
  # Paths
  config_dir: Path = field(default_factory=lambda: Path.home() / ".boilerplates")
  cache_dir: Path = field(default_factory=lambda: Path.home() / ".boilerplates" / "cache")
  
  # Libraries
  libraries: List[LibraryConfig] = field(default_factory=list)
  
  # Application settings
  log_level: str = "INFO"
  default_editor: str = "vim"
  auto_update_remotes: bool = False
  template_validation: bool = True
  
  # UI settings
  use_rich_output: bool = True
  confirm_generation: bool = True
  show_summary: bool = True
  
  def __post_init__(self):
    """Ensure directories exist."""
    self.config_dir.mkdir(parents=True, exist_ok=True)
    self.cache_dir.mkdir(parents=True, exist_ok=True)
  
  @classmethod
  def load(cls, config_path=None):
    """Load configuration from file or use defaults.
    
    Args:
        config_path: Optional path to config file. If not provided,
                    uses ~/.boilerplates/config.yaml
    
    Returns:
        Config instance with loaded or default values
    """
    if config_path is None:
      config_path = Path.home() / ".boilerplates" / "config.yaml"
    
    if config_path.exists():
      try:
        with open(config_path, 'r') as f:
          data = yaml.safe_load(f) or {}
        
        # Parse libraries if present
        libraries = []
        for lib_data in data.get('libraries', []):
          try:
            libraries.append(LibraryConfig(**lib_data))
          except TypeError as e:
            logger.warning(f"Invalid library configuration: {lib_data}, error: {e}")
        
        # Remove libraries from data to avoid duplicate in Config init
        if 'libraries' in data:
          del data['libraries']
        
        # Convert path strings to Path objects
        if 'config_dir' in data:
          data['config_dir'] = Path(data['config_dir'])
        if 'cache_dir' in data:
          data['cache_dir'] = Path(data['cache_dir'])
        
        config = cls(**data, libraries=libraries)
        logger.debug(f"Loaded configuration from {config_path}")
        return config
        
      except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML format in config.yaml: {e}")
      except Exception as e:
        logger.warning(f"Failed to load config from {config_path}: {e}, using defaults")
        return cls()
    else:
      logger.debug(f"No config file found at {config_path}, using defaults")
      return cls()
  
  def save(self, config_path=None):
    """Save configuration to file.
    
    Args:
        config_path: Optional path to save config. If not provided,
                    uses ~/.boilerplates/config.yaml
    """
    if config_path is None:
      config_path = self.config_dir / "config.yaml"
    
    data = {
      'config_dir': str(self.config_dir),
      'cache_dir': str(self.cache_dir),
      'log_level': self.log_level,
      'default_editor': self.default_editor,
      'auto_update_remotes': self.auto_update_remotes,
      'template_validation': self.template_validation,
      'use_rich_output': self.use_rich_output,
      'confirm_generation': self.confirm_generation,
      'show_summary': self.show_summary,
      'libraries': [
        {
          'name': lib.name,
          'type': lib.type,
          'path': lib.path,
          'repo': lib.repo,
          'branch': lib.branch,
          'priority': lib.priority
        }
        for lib in self.libraries
      ]
    }
    
    # Remove None values from library configs
    for lib in data['libraries']:
      lib = {k: v for k, v in lib.items() if v is not None}
    
    try:
      config_path.parent.mkdir(parents=True, exist_ok=True)
      with open(config_path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
      logger.debug(f"Saved configuration to {config_path}")
    except Exception as e:
      raise OSError(f"Failed to save config.yaml: {e}")
  
  def add_library(self, library):
    """Add a library configuration.
    
    Args:
        library: LibraryConfig instance to add
    """
    # Check for duplicate names
    existing_names = {lib.name for lib in self.libraries}
    if library.name in existing_names:
      raise ValueError(f"Library with name '{library.name}' already exists")
    
    self.libraries.append(library)
    # Sort by priority (highest first)
    self.libraries.sort(key=lambda l: l.priority, reverse=True)
  
  def remove_library(self, name):
    """Remove a library configuration by name.
    
    Args:
        name: Name of the library to remove
        
    Returns:
        True if library was removed, False if not found
    """
    original_count = len(self.libraries)
    self.libraries = [lib for lib in self.libraries if lib.name != name]
    return len(self.libraries) < original_count
  
  def get_library(self, name):
    """Get a library configuration by name.
    
    Args:
        name: Name of the library
        
    Returns:
        LibraryConfig if found, None otherwise
    """
    for lib in self.libraries:
      if lib.name == name:
        return lib
    return None


# Global configuration instance
_config = None


def get_config():
  """Get the global configuration instance.
  
  Returns:
      The global Config instance, loading it if necessary
  """
  global _config
  if _config is None:
    _config = Config.load()
  return _config


def set_config(config):
  """Set the global configuration instance.
  
  Args:
      config: Config instance to use globally
  """
  global _config
  _config = config
