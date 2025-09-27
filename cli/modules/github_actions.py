from __future__ import annotations

from ..core.module import Module
from ..core.registry import registry

class GitHubActionsModule(Module):
  """Module for managing GitHub Actions workflows."""
  
  name: str = "github-actions"
  description: str = "Manage GitHub Actions workflows"
  files: list[str] = ["action.yml", "action.yaml", "workflow.yml", "workflow.yaml"]

# Register the module
registry.register(GitHubActionsModule)
