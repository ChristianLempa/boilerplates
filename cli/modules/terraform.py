from ..core.module import Module
from ..core.registry import registry

class TerraformModule(Module):
  """Terraform module."""
  
  name = "terraform"
  description = "Manage Terraform configurations"
  files = ["main.tf", "variables.tf", "outputs.tf", "versions.tf"]

# Register the module
registry.register(TerraformModule)
