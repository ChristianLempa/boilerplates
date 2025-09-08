from ..core.module import Module
from ..core.registry import registry

class KestraModule(Module):
  """Module for managing Kestra workflows and configurations."""
  
  name = "kestra"
  description = "Manage Kestra workflows and configurations"
  files = ["inputs.yaml", "variables.yaml", "webhook.yaml", "flow.yml", "flow.yaml"]

# Register the module
registry.register(KestraModule)
