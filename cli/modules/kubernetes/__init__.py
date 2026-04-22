"""Kubernetes module."""

from ...core.module import Module
from ...core.registry import registry


class KubernetesModule(Module):
    """Kubernetes module."""

    name = "kubernetes"
    description = "Manage Kubernetes configurations"


registry.register(KubernetesModule)
