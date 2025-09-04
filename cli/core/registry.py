"""Module registry system with decorator-based registration."""
from typing import Type, Dict, List
from functools import wraps


class Registry:
  """Registry using decorators for explicit module registration."""
  
  def __init__(self):
    self._modules: Dict[str, Type] = {}
    self._configs: Dict[str, Dict] = {}

  def register_module(self, name: str = None, description: str = None, files: List[str] = None, enabled: bool = True, **kwargs):
    """Decorator to register a module class with automatic configuration."""
    def decorator(cls: Type):
      module_name = name or cls.__name__.replace("Module", "").lower()
      config = {
        'name': module_name,
        'description': description or f"Manage {module_name} configurations",
        'files': files or [],
        'enabled': enabled,
        **kwargs
      }
      
      original_init = cls.__init__
      
      @wraps(original_init)
      def enhanced_init(self, *args, **init_kwargs):
        if not hasattr(self, '_configured'):
          for attr, value in config.items():
            if not hasattr(self, attr) or not getattr(self, attr):
              setattr(self, attr, value)
          self._configured = True
        original_init(self, *args, **init_kwargs)
      
      cls.__init__ = enhanced_init
      cls._module_name = module_name
      cls._module_config = config
      
      if enabled:
        self._modules[module_name] = cls
        self._configs[module_name] = config
      
      return cls
    return decorator
  
  def get_module_configs(self) -> Dict[str, Dict]:
    """Get all module configurations."""
    return self._configs.copy()
  
  def create_instances(self) -> List:
    """Create instances of all registered modules, sorted alphabetically."""
    instances = []
    for name, cls in sorted(self._modules.items()):
      try:
        instances.append(cls())
      except Exception as e:
        print(f"Warning: Could not instantiate {cls.__name__}: {e}")
    return instances


# Global registry instance
registry = Registry()
register_module = registry.register_module
