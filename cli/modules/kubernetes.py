from ..core.module import Module
from ..core.registry import register_module

@register_module(
  name="kubernetes",
  description="Manage Kubernetes manifests and configurations",
  files=["deployment.yml", "deployment.yaml", "service.yml", "service.yaml", "manifest.yml", "manifest.yaml", "values.yml", "values.yaml"],
  priority=5,
  dependencies=["docker"]
)
class KubernetesModule(Module):
  """Module for managing Kubernetes manifests and configurations."""

  def __init__(self):
    super().__init__(name=self.name, description=self.description, files=self.files)

  def register(self, app):
    return super().register(app)
