from __future__ import annotations

from ..core.module import Module
from ..core.registry import registry

class VagrantModule(Module):
  """Module for managing Vagrant configurations and files."""
  
  name: str = "vagrant"
  description: str = "Manage Vagrant configurations and files"
  files: list[str] = ["Vagrantfile", "vagrantfile"]

# Register the module
registry.register(VagrantModule)
