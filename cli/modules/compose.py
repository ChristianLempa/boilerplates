from ..core.module import Module
from ..core.registry import registry

class ComposeModule(Module):
  """Docker Compose module."""
  
  name = "compose"
  description = "Manage Docker Compose configurations"
  files = ["docker-compose.yml", "compose.yml", "compose.yaml"]

# Register the module
registry.register(ComposeModule)
