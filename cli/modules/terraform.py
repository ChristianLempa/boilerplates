from __future__ import annotations

from ..core.module import Module
from ..core.registry import registry

class TerraformModule(Module):
  """Terraform module."""
  
  name: str = "terraform"
  description: str = "Manage Terraform configurations"

# Register the module
registry.register(TerraformModule)
