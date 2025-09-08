from ..core.module import Module
from ..core.registry import registry

class PackerModule(Module):
  """Module for managing Packer templates and configurations."""
  
  name = "packer"
  description = "Manage Packer templates and configurations"
  files = ["template.pkr.hcl", "build.pkr.hcl", "variables.pkr.hcl", "sources.pkr.hcl"]

# Register the module
registry.register(PackerModule)
