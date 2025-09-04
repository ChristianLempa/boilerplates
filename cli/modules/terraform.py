from ..core.module import Module
from ..core.registry import register_module

@register_module(
  name="terraform",
  description="Manage Terraform configurations and modules",
  files=["main.tf", "variables.tf", "outputs.tf", "versions.tf", "providers.tf", "terraform.tf"]
)
class TerraformModule(Module):
  """Module for managing Terraform configurations and modules."""

  def __init__(self):
    super().__init__(name=self.name, description=self.description, files=self.files)

  def register(self, app):
    return super().register(app)
