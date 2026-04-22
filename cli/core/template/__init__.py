"""Template package for template and variable management.

This package provides Template, VariableCollection, VariableSection, and Variable
classes for managing templates and their variables.
"""

from .template import (
    Template,
    TemplateErrorHandler,
    TemplateFile,
    TemplateMetadata,
    TemplateVersionMetadata,
    normalize_template_slug,
)
from .variable import Variable
from .variable_collection import VariableCollection
from .variable_section import VariableSection

__all__ = [
    "Template",
    "TemplateErrorHandler",
    "TemplateFile",
    "TemplateMetadata",
    "TemplateVersionMetadata",
    "Variable",
    "VariableCollection",
    "VariableSection",
    "normalize_template_slug",
]
