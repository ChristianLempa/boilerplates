"""Template package for template and variable management.

This package provides Template, VariableCollection, VariableSection, and Variable
classes for managing templates and their variables.
"""

from .template import Template, TemplateMetadata, TemplateFile, TemplateErrorHandler
from .variable_collection import VariableCollection
from .variable_section import VariableSection
from .variable import Variable

__all__ = [
    "Template",
    "TemplateMetadata",
    "TemplateFile",
    "TemplateErrorHandler",
    "VariableCollection",
    "VariableSection",
    "Variable",
]
