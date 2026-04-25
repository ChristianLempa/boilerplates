"""Terraform module."""

from ...core.module import Module
from ...core.registry import registry
from ...core.validation import TerraformValidator


class TerraformModule(Module):
    """Terraform module."""

    name = "terraform"
    description = "Manage Terraform configurations"
    kind_validator_class = TerraformValidator


registry.register(TerraformModule)
