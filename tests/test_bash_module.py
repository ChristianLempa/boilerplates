"""Tests for the Bash template module."""

from __future__ import annotations

import cli.modules.bash  # noqa: F401 - import registers the module
from cli.core.registry import registry
from cli.modules.bash import BashModule


def test_bash_module_metadata() -> None:
    """The Bash module should expose the expected CLI metadata."""
    assert BashModule.name == "bash"
    assert BashModule.description == "Manage Bash script and automation templates"


def test_bash_module_registers_with_registry() -> None:
    """Importing the module should make the Bash kind discoverable."""
    registered_modules = dict(registry.iter_module_classes())

    assert registered_modules["bash"] is BashModule
