from __future__ import annotations

from ..core.module import Module
from ..core.registry import registry

class AnsibleModule(Module):
  """Module for managing Ansible playbooks and configurations."""
  
  name: str = "ansible"
  description: str = "Manage Ansible playbooks and configurations"
  files: list[str] = ["playbook.yml", "playbook.yaml", "main.yml", "main.yaml", 
                      "site.yml", "site.yaml"]

registry.register(AnsibleModule)
