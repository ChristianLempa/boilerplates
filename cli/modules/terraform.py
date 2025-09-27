from __future__ import annotations

from ..core.module import Module
from ..core.registry import registry

class TerraformModule(Module):
  """Terraform module."""
  
  name: str = "terraform"
  description: str = "Manage Terraform configurations"
  files: list[str] = ["main.tf", "variables.tf", "outputs.tf", "versions.tf"]

# Register the module
registry.register(TerraformModule)
