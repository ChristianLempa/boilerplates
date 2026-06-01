"""Python templates module."""

from ...core.module import Module
from ...core.registry import registry


class PythonModule(Module):
    """Python templates module."""

    name = "python"
    description = "Manage Python project and automation templates"


registry.register(PythonModule)
