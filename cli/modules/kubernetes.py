from __future__ import annotations

from ..core.module import Module
from ..core.registry import registry

class KubernetesModule(Module):
  """Module for managing Kubernetes manifests and configurations."""
  
  name: str = "kubernetes"
  description: str = "Manage Kubernetes manifests and configurations"
  files: list[str] = ["deployment.yml", "deployment.yaml", "service.yml", "service.yaml", 
                      "manifest.yml", "manifest.yaml", "values.yml", "values.yaml"]

# Register the module
registry.register(KubernetesModule)
