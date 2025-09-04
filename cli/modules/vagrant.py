from ..core.module import Module
from ..core.registry import register_module

@register_module(
  name="vagrant",
  description="Manage Vagrant configurations and files",
  files=["Vagrantfile", "vagrantfile"]
)
class VagrantModule(Module):
  """Module for managing Vagrant configurations and files."""

  def __init__(self):
    super().__init__(name=self.name, description=self.description, files=self.files)

  def register(self, app):
    return super().register(app)
