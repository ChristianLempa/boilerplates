"""Kubernetes module."""

import logging

from ...core.module import Module
from ...core.registry import registry

logger = logging.getLogger(__name__)


class KubernetesModule(Module):
    """Kubernetes module."""

    name = "kubernetes"
    description = "Manage Kubernetes configurations"


registry.register(KubernetesModule)
