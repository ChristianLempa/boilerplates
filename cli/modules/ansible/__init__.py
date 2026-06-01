"""Ansible module."""

from ...core.module import Module
from ...core.registry import registry
from ...core.validation import AnsibleValidator


class AnsibleModule(Module):
    """Ansible module."""

    name = "ansible"
    description = "Manage Ansible configurations"
    kind_validator_class = AnsibleValidator


registry.register(AnsibleModule)
