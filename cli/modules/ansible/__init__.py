"""Ansible module."""

import logging

from ...core.module import Module
from ...core.registry import registry

logger = logging.getLogger(__name__)


class AnsibleModule(Module):
    """Ansible module."""

    name = "ansible"
    description = "Manage Ansible configurations"


registry.register(AnsibleModule)
