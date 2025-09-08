from ..core.module import Module
from ..core.registry import registry

class GitLabCIModule(Module):
  """Module for managing GitLab CI/CD pipelines."""
  
  name = "gitlab-ci"
  description = "Manage GitLab CI/CD pipelines"
  files = [".gitlab-ci.yml", ".gitlab-ci.yaml", "gitlab-ci.yml", "gitlab-ci.yaml"]

# Register the module
registry.register(GitLabCIModule)
