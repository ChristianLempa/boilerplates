"""Template package for template and variable management.

This package provides Template, VariableCollection, VariableSection, and Variable
classes for managing templates and their variables.
"""

from .template import Template, TemplateErrorHandler, TemplateFile, TemplateMetadata
from .variable import Variable
from .variable_collection import VariableCollection
from .variable_section import VariableSection

__all__ = [
    "Template",
    "TemplateErrorHandler",
    "TemplateFile",
    "TemplateMetadata",
    "Variable",
    "VariableCollection",
    "VariableSection",
]
