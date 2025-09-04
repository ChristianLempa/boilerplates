from ..core.module import Module
from ..core.registry import register_module

@register_module(
  name="gitlab-ci",
  description="Manage GitLab CI/CD pipelines",
  files=[".gitlab-ci.yml", ".gitlab-ci.yaml", "gitlab-ci.yml", "gitlab-ci.yaml"]
)
class GitLabCIModule(Module):
  """Module for managing GitLab CI/CD pipelines."""

  def __init__(self):
    super().__init__(name=self.name, description=self.description, files=self.files)

  def register(self, app):
    return super().register(app)
