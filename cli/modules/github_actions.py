from __future__ import annotations

from ..core.module import Module
from ..core.registry import registry

class GitHubActionsModule(Module):
  """Module for managing GitHub Actions workflows."""
  
  name: str = "github-actions"
  description: str = "Manage GitHub Actions workflows"

# Register the module
registry.register(GitHubActionsModule)
