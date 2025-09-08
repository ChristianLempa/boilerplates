from ..core.module import Module
from ..core.registry import registry

class GitHubActionsModule(Module):
  """Module for managing GitHub Actions workflows."""
  
  name = "github-actions"
  description = "Manage GitHub Actions workflows"
  files = ["action.yml", "action.yaml", "workflow.yml", "workflow.yaml"]

# Register the module
registry.register(GitHubActionsModule)
