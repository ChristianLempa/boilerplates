from ..core.module import Module
from ..core.registry import register_module

@register_module(
  name="kestra",
  description="Manage Kestra workflows and configurations",
  files=["inputs.yaml", "variables.yaml", "webhook.yaml", "flow.yml", "flow.yaml"]
)
class KestraModule(Module):
  """Module for managing Kestra workflows and configurations."""

  def __init__(self):
    super().__init__(name=self.name, description=self.description, files=self.files)

  def register(self, app):
    return super().register(app)
