from ..core.module import Module
from ..core.registry import register_module

@register_module(
  name="packer",
  description="Manage Packer templates and configurations",
  files=["template.pkr.hcl", "build.pkr.hcl", "variables.pkr.hcl", "sources.pkr.hcl"]
)
class PackerModule(Module):
  """Module for managing Packer templates and configurations."""

  def __init__(self):
    super().__init__(name=self.name, description=self.description, files=self.files)

  def register(self, app):
    return super().register(app)
