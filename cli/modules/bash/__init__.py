"""Bash templates module."""

from ...core.module import Module
from ...core.registry import registry


class BashModule(Module):
    """Bash templates module."""

    name = "bash"
    description = "Manage Bash script and automation templates"


registry.register(BashModule)
