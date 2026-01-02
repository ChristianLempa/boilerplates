"""Helm module."""

import logging

from ...core.module import Module
from ...core.registry import registry

logger = logging.getLogger(__name__)


class HelmModule(Module):
    """Helm module."""

    name = "helm"
    description = "Manage Helm configurations"


registry.register(HelmModule)
