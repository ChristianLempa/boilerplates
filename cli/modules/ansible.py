from ..core.module import Module
from ..core.registry import register_module

@register_module(
  name="ansible",
  description="Manage Ansible playbooks and configurations",
  files=["playbook.yml", "playbook.yaml", "main.yml", "main.yaml", "site.yml", "site.yaml"],
  priority=8
)
class AnsibleModule(Module):
  """Module for managing Ansible playbooks and configurations."""

  def __init__(self):
    super().__init__(name=self.name, description=self.description, files=self.files)

  def register(self, app):
    return super().register(app)
