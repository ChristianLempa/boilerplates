"""Static templates module."""

from ...core.module import Module
from ...core.registry import registry


class StaticModule(Module):
    """Static templates module."""

    name = "static"
    description = "Manage static file templates"


registry.register(StaticModule)
