"""Docker Compose module with multi-schema support."""

from ...core.module import Module
from ...core.registry import registry

# Import schema specifications
from .spec_v1_0 import spec as spec_1_0
from .spec_v1_1 import spec as spec_1_1

# Schema version mapping
SCHEMAS = {
  "1.0": spec_1_0,
  "1.1": spec_1_1,
}

# Default spec points to latest version
spec = spec_1_1


class ComposeModule(Module):
  """Docker Compose module."""

  name = "compose"
  description = "Manage Docker Compose configurations"
  schema_version = "1.1"  # Current schema version supported by this module
  schemas = SCHEMAS  # Available schema versions


registry.register(ComposeModule)
