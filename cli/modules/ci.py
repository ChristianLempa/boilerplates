from __future__ import annotations

from ..core.module import Module
from ..core.registry import registry

class CIModule(Module):
  """Module for managing CI/CD automation templates."""
  
  name: str = "ci"
  description: str = "Manage CI/CD automation templates (GitHub Actions, GitLab CI, Kestra)"

# Register the module
registry.register(CIModule)
