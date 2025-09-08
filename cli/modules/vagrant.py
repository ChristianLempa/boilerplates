from ..core.module import Module
from ..core.registry import registry

class VagrantModule(Module):
  """Module for managing Vagrant configurations and files."""
  
  name = "vagrant"
  description = "Manage Vagrant configurations and files"
  files = ["Vagrantfile", "vagrantfile"]

# Register the module
registry.register(VagrantModule)
