"""Module registry system."""
import logging

logger = logging.getLogger(__name__)


class ModuleRegistry:
  """Simple module registry without magic."""
  
  def __init__(self):
    self._modules = {}
    logger.debug("Initializing module registry")
  
  def register(self, module_class):
    """Register a module class."""
    # Module class defines its own name attribute
    logger.debug(f"Attempting to register module class '{module_class.name}'")
    
    if module_class.name in self._modules:
      logger.warning(f"Module '{module_class.name}' already registered, replacing with new implementation")
    
    self._modules[module_class.name] = module_class
    logger.info(f"Registered module '{module_class.name}' (total modules: {len(self._modules)})")
    logger.debug(f"Module '{module_class.name}' details: description='{module_class.description}', files={module_class.files}")
  
  def create_instances(self):
    """Create instances of all registered modules."""
    logger.info(f"Creating instances for {len(self._modules)} registered modules")
    instances = []
    failed_modules = []
    
    for name in sorted(self._modules.keys()):
      try:
        logger.debug(f"Attempting to create instance of module '{name}'")
        instance = self._modules[name]()
        instances.append(instance)
        logger.debug(f"Successfully instantiated module '{name}'")
      except Exception as e:
        logger.error(f"Failed to instantiate module '{name}': {e}")
        failed_modules.append(name)
        print(f"Warning: Could not instantiate {name}: {e}")
    
    if failed_modules:
      logger.warning(f"Failed to instantiate {len(failed_modules)} modules: {failed_modules}")
    
    logger.info(f"Successfully created {len(instances)} module instances out of {len(self._modules)} registered")
    if instances:
      logger.debug(f"Active modules: {[inst.name for inst in instances]}")
    return instances

# Global registry
registry = ModuleRegistry()
