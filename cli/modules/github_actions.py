from ..core.module import Module
from ..core.registry import register_module

@register_module(
  name="github-actions",
  description="Manage GitHub Actions workflows",
  files=["action.yml", "action.yaml", "workflow.yml", "workflow.yaml"]
)
class GitHubActionsModule(Module):
  """Module for managing GitHub Actions workflows."""

  def __init__(self):
    super().__init__(name=self.name, description=self.description, files=self.files)

  def register(self, app):
    return super().register(app)
