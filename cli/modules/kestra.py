from __future__ import annotations

from ..core.module import Module
from ..core.registry import registry

class KestraModule(Module):
  """Module for managing Kestra workflows and configurations."""
  
  name: str = "kestra"
  description: str = "Manage Kestra workflows and configurations"
  files: list[str] = ["inputs.yaml", "variables.yaml", "webhook.yaml", "flow.yml", "flow.yaml"]

# Register the module
registry.register(KestraModule)
