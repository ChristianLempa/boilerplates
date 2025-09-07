"""Module registry system."""


class ModuleRegistry:
  """Simple module registry without magic."""
  
  def __init__(self):
    self._modules = {}
  
  def register(self, module_class):
    """Register a module class."""
    # Module class defines its own name attribute
    self._modules[module_class.name] = module_class
  
  def create_instances(self):
    """Create instances of all registered modules."""
    instances = []
    for name in sorted(self._modules.keys()):
      try:
        instances.append(self._modules[name]())
      except Exception as e:
        print(f"Warning: Could not instantiate {name}: {e}")
    return instances

# Global registry
registry = ModuleRegistry()
