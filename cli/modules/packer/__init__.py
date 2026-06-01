"""Packer module."""

from ...core.module import Module
from ...core.registry import registry
from ...core.validation import PackerValidator


class PackerModule(Module):
    """Packer module."""

    name = "packer"
    description = "Manage Packer configurations"
    kind_validator_class = PackerValidator


registry.register(PackerModule)
