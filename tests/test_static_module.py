"""Tests for the static template module."""

from __future__ import annotations

import cli.modules.static  # noqa: F401 - import registers the module
from cli.core.registry import registry
from cli.modules.static import StaticModule


def test_static_module_metadata() -> None:
    """The static module should expose the expected CLI metadata."""
    assert StaticModule.name == "static"
    assert StaticModule.description == "Manage static file templates"


def test_static_module_registers_with_registry() -> None:
    """Importing the module should make the static kind discoverable."""
    registered_modules = dict(registry.iter_module_classes())

    assert registered_modules["static"] is StaticModule
