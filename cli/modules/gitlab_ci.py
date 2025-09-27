from __future__ import annotations

from ..core.module import Module
from ..core.registry import registry

class GitLabCIModule(Module):
  """Module for managing GitLab CI/CD pipelines."""
  
  name: str = "gitlab-ci"
  description: str = "Manage GitLab CI/CD pipelines"
  files: list[str] = [".gitlab-ci.yml", ".gitlab-ci.yaml", "gitlab-ci.yml", "gitlab-ci.yaml"]

# Register the module
registry.register(GitLabCIModule)
