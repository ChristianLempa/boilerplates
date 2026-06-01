"""Helm module."""

from ...core.module import Module
from ...core.registry import registry
from ...core.validation import HelmValidator


class HelmModule(Module):
    """Helm module."""

    name = "helm"
    description = "Manage Helm configurations"
    kind_validator_class = HelmValidator


registry.register(HelmModule)
