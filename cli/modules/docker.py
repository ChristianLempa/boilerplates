from ..core.module import Module
from ..core.registry import register_module

@register_module(
  name="docker",
  description="Manage Docker configurations and files",
  files=["Dockerfile", "dockerfile", ".dockerignore"]
)
class DockerModule(Module):
  """Module for managing Docker configurations and files."""

  def __init__(self):
    super().__init__(name=self.name, description=self.description, files=self.files)

  def register(self, app):
    return super().register(app)
