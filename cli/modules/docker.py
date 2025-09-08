from ..core.module import Module
from ..core.registry import registry

class DockerModule(Module):
  """Module for managing Docker configurations and files."""
  
  name = "docker"
  description = "Manage Docker configurations and files"
  files = ["Dockerfile", "dockerfile", ".dockerignore"]

# Register the module
registry.register(DockerModule)
