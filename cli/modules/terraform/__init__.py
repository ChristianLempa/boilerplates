"""Terraform module."""

import logging

from ...core.module import Module
from ...core.registry import registry

logger = logging.getLogger(__name__)


class TerraformModule(Module):
    """Terraform module."""

    name = "terraform"
    description = "Manage Terraform configurations"


registry.register(TerraformModule)
