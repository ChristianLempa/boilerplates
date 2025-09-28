from __future__ import annotations

from ..core.module import Module
from ..core.registry import registry

class DockerModule(Module):
  """Module for managing Docker configurations and files."""
  
  name: str = "docker"
  description: str = "Manage Docker configurations and files"

# Register the module
registry.register(DockerModule)
