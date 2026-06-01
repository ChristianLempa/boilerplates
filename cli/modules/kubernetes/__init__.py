"""Kubernetes module."""

from ...core.module import Module
from ...core.registry import registry
from ...core.validation import KubernetesValidator


class KubernetesModule(Module):
    """Kubernetes module."""

    name = "kubernetes"
    description = "Manage Kubernetes configurations"
    kind_validator_class = KubernetesValidator


registry.register(KubernetesModule)
