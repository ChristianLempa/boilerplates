"""Terraform module."""

from ...core.module import Module
from ...core.registry import registry


class TerraformModule(Module):
    """Terraform module."""

    name = "terraform"
    description = "Manage Terraform configurations"


registry.register(TerraformModule)
