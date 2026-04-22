"""Helm module."""

from ...core.module import Module
from ...core.registry import registry


class HelmModule(Module):
    """Helm module."""

    name = "helm"
    description = "Manage Helm configurations"


registry.register(HelmModule)
