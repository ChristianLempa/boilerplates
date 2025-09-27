"""Module registry system."""
from __future__ import annotations

import logging
from typing import Iterator, Type

logger = logging.getLogger(__name__)


# ------------------------------
# SECTION: ModuleRegistry Class
# ------------------------------

class ModuleRegistry:
  """Simple module registry without magic."""
  
  def __init__(self) -> None:
    self._modules = {}
    logger.debug("Initializing module registry")
  
  def register(self, module_class: Type) -> None:
    """Register a module class."""
    # Module class defines its own name attribute
    logger.debug(f"Attempting to register module class '{module_class.name}'")
    
    if module_class.name in self._modules:
      logger.warning(f"Module '{module_class.name}' already registered, replacing with new implementation")
    
    self._modules[module_class.name] = module_class
    logger.info(f"Registered module '{module_class.name}' (total modules: {len(self._modules)})")
    logger.debug(f"Module '{module_class.name}' details: description='{module_class.description}', files={module_class.files}")
  
  def iter_module_classes(self) -> Iterator[tuple[str, Type]]:
    """Yield registered module classes without instantiating them."""
    logger.debug(f"Iterating over {len(self._modules)} registered module classes")
    for name in sorted(self._modules.keys()):
      yield name, self._modules[name]

# !SECTION

# -------------------------
# SECTION: Global Instance
# -------------------------

# Global registry
registry = ModuleRegistry()

# !SECTION
