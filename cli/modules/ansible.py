from ..core.module import Module
from ..core.registry import registry

class AnsibleModule(Module):
  """Module for managing Ansible playbooks and configurations."""
  
  name = "ansible"
  description = "Manage Ansible playbooks and configurations"
  files = ["playbook.yml", "playbook.yaml", "main.yml", "main.yaml", 
           "site.yml", "site.yaml"]

# Register the module
registry.register(AnsibleModule)
