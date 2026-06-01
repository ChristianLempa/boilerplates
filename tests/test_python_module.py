"""Tests for the Python template module."""

from __future__ import annotations

import cli.modules.python  # noqa: F401 - import registers the module
from cli.core.registry import registry
from cli.modules.python import PythonModule


def test_python_module_metadata() -> None:
    """The Python module should expose the expected CLI metadata."""
    assert PythonModule.name == "python"
    assert PythonModule.description == "Manage Python project and automation templates"


def test_python_module_registers_with_registry() -> None:
    """Importing the module should make the Python kind discoverable."""
    registered_modules = dict(registry.iter_module_classes())

    assert registered_modules["python"] is PythonModule
