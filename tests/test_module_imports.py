"""Test that all modules can be imported successfully."""

import sys

from cli.core.module import Module
from cli.core.registry import registry
from cli.core.template import Template
from cli.core.template.variable import Variable
from cli.modules.compose import ComposeModule


def test_compose_module_import():
    """Test that compose module imports without errors."""
    # This test verifies the fix for Python 3.9 compatibility issue
    # where union type syntax (str | None) caused import errors
    assert ComposeModule is not None
    assert ComposeModule.name == "compose"


def test_all_modules_import():
    """Test that all core modules can be imported."""
    # Test core modules
    assert Module is not None
    assert registry is not None
    assert Template is not None
    assert Variable is not None


def test_python_version_requirement():
    """Test that we're running on Python 3.10+."""
    assert sys.version_info >= (3, 10), (
        f"Python 3.10+ is required, but running {sys.version_info.major}.{sys.version_info.minor}"
    )
