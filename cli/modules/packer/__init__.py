"""Packer module."""

import logging

from ...core.module import Module
from ...core.registry import registry

logger = logging.getLogger(__name__)


class PackerModule(Module):
    """Packer module."""

    name = "packer"
    description = "Manage Packer configurations"


registry.register(PackerModule)
