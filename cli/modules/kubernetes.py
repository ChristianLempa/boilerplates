from ..core.module import Module
from ..core.registry import registry

class KubernetesModule(Module):
  """Module for managing Kubernetes manifests and configurations."""
  
  name = "kubernetes"
  description = "Manage Kubernetes manifests and configurations"
  files = ["deployment.yml", "deployment.yaml", "service.yml", "service.yaml", 
           "manifest.yml", "manifest.yaml", "values.yml", "values.yaml"]

# Register the module
registry.register(KubernetesModule)
