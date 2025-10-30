"""Helm module with multi-schema support."""

from ...core.module import Module
from ...core.registry import registry

# Import schema specifications
from .spec_v1_0 import spec as spec_1_0

# Schema version mapping
SCHEMAS = {
    "1.0": spec_1_0,
}

# Default spec points to latest version
spec = spec_1_0


class HelmModule(Module):
    """Helm module."""

    name = "helm"
    description = "Manage Helm charts"
    schema_version = "1.0"  # Current schema version supported by this module
    schemas = SCHEMAS  # Available schema versions


registry.register(HelmModule)
