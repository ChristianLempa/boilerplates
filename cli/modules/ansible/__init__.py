"""Ansible module."""

from ...core.module import Module
from ...core.registry import registry


class AnsibleModule(Module):
    """Ansible module."""

    name = "ansible"
    description = "Manage Ansible configurations"


registry.register(AnsibleModule)
