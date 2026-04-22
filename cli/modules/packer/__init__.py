"""Packer module."""

from ...core.module import Module
from ...core.registry import registry


class PackerModule(Module):
    """Packer module."""

    name = "packer"
    description = "Manage Packer configurations"


registry.register(PackerModule)
