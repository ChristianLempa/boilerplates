"""Template package for template and variable management.

This package provides Template, VariableCollection, VariableSection, and Variable
classes for managing templates and their variables.
"""

from .template import (
    TEMPLATE_STATUS_DRAFT,
    TEMPLATE_STATUS_INVALID,
    TEMPLATE_STATUS_PUBLISHED,
    Template,
    TemplateErrorHandler,
    TemplateFile,
    TemplateMetadata,
)
from .variable import Variable
from .variable_collection import VariableCollection
from .variable_section import VariableSection

__all__ = [
    "TEMPLATE_STATUS_DRAFT",
    "TEMPLATE_STATUS_INVALID",
    "TEMPLATE_STATUS_PUBLISHED",
    "Template",
    "TemplateErrorHandler",
    "TemplateFile",
    "TemplateMetadata",
    "Variable",
    "VariableCollection",
    "VariableSection",
]
