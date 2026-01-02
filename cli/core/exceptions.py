"""Custom exception classes for the boilerplates CLI.

This module defines specific exception types for better error handling
and diagnostics throughout the application.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class BoilerplatesError(Exception):
    """Base exception for all boilerplates CLI errors."""

    pass


class ConfigError(BoilerplatesError):
    """Raised when configuration operations fail."""

    pass


class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""

    pass


class TemplateError(BoilerplatesError):
    """Base exception for template-related errors."""

    pass


class TemplateNotFoundError(TemplateError):
    """Raised when a template cannot be found."""

    def __init__(self, template_id: str, module_name: str | None = None):
        self.template_id = template_id
        self.module_name = module_name
        msg = f"Template '{template_id}' not found"
        if module_name:
            msg += f" in module '{module_name}'"
        super().__init__(msg)


class TemplateDraftError(TemplateError):
    """Raised when attempting to use a draft template."""

    def __init__(self, template_id: str, module_name: str | None = None):
        self.template_id = template_id
        self.module_name = module_name

        module_suffix = f" in module '{module_name}'" if module_name else ""
        msg = (
            f"Template '{template_id}' is in draft mode and not yet available for use{module_suffix}.\n"
            "Draft templates are work-in-progress and cannot be generated yet.\n"
            "To get updates when published, run 'boilerplates repo update' to sync your library."
        )
        super().__init__(msg)


class DuplicateTemplateError(TemplateError):
    """Raised when duplicate template IDs are found within the same library."""

    def __init__(self, template_id: str, library_name: str):
        self.template_id = template_id
        self.library_name = library_name
        super().__init__(
            f"Duplicate template ID '{template_id}' found in library '{library_name}'. "
            f"Each template within a library must have a unique ID."
        )


class TemplateLoadError(TemplateError):
    """Raised when a template fails to load."""

    pass


class TemplateSyntaxError(TemplateError):
    """Raised when a Jinja2 template has syntax errors."""

    def __init__(self, template_id: str, errors: list[str]):
        self.template_id = template_id
        self.errors = errors
        msg = f"Jinja2 syntax errors in template '{template_id}':\n" + "\n".join(errors)
        super().__init__(msg)


class TemplateValidationError(TemplateError):
    """Raised when template validation fails."""

    pass


class IncompatibleSchemaVersionError(TemplateError):
    """Raised when a template uses a schema version not supported by the module."""

    def __init__(
        self,
        template_id: str,
        template_schema: str,
        module_schema: str,
        module_name: str,
    ):
        self.template_id = template_id
        self.template_schema = template_schema
        self.module_schema = module_schema
        self.module_name = module_name
        msg = (
            f"Template '{template_id}' uses schema version {template_schema}, "
            f"but module '{module_name}' only supports up to version {module_schema}.\n\n"
            f"This template requires features not available in your current CLI version.\n"
            f"Please upgrade the boilerplates CLI.\n\n"
            f"Run: pip install --upgrade boilerplates"
        )
        super().__init__(msg)


@dataclass
class RenderErrorContext:
    """Context information for template rendering errors."""

    file_path: str | None = None
    line_number: int | None = None
    column: int | None = None
    context_lines: list[str] = field(default_factory=list)
    variable_context: dict[str, str] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    original_error: Exception | None = None


class TemplateRenderError(TemplateError):
    """Raised when template rendering fails."""

    def __init__(self, message: str, context: RenderErrorContext | None = None):
        self.context = context or RenderErrorContext()

        # Expose context fields as instance attributes for backward compatibility
        self.file_path = self.context.file_path
        self.line_number = self.context.line_number
        self.column = self.context.column
        self.context_lines = self.context.context_lines
        self.variable_context = self.context.variable_context
        self.suggestions = self.context.suggestions
        self.original_error = self.context.original_error

        # Build enhanced error message
        parts = [message]

        if self.context.file_path:
            location = f"File: {self.context.file_path}"
            if self.context.line_number:
                location += f", Line: {self.context.line_number}"
                if self.context.column:
                    location += f", Column: {self.context.column}"
            parts.append(location)

        super().__init__("\n".join(parts))


class VariableError(BoilerplatesError):
    """Base exception for variable-related errors."""

    pass


class VariableValidationError(VariableError):
    """Raised when variable validation fails."""

    def __init__(self, variable_name: str, message: str):
        self.variable_name = variable_name
        msg = f"Validation error for variable '{variable_name}': {message}"
        super().__init__(msg)


class VariableTypeError(VariableError):
    """Raised when a variable has an incorrect type."""

    def __init__(self, variable_name: str, expected_type: str, actual_type: str):
        self.variable_name = variable_name
        self.expected_type = expected_type
        self.actual_type = actual_type
        msg = f"Type error for variable '{variable_name}': expected {expected_type}, got {actual_type}"
        super().__init__(msg)


class LibraryError(BoilerplatesError):
    """Raised when library operations fail."""

    pass


class ModuleError(BoilerplatesError):
    """Raised when module operations fail."""

    pass


class ModuleNotFoundError(ModuleError):
    """Raised when a module cannot be found."""

    def __init__(self, module_name: str):
        self.module_name = module_name
        msg = f"Module '{module_name}' not found"
        super().__init__(msg)


class ModuleLoadError(ModuleError):
    """Raised when a module fails to load."""

    pass


class SchemaError(BoilerplatesError):
    """Raised when schema operations fail."""

    def __init__(self, message: str, details: str | None = None):
        self.details = details
        msg = message
        if details:
            msg += f" ({details})"
        super().__init__(msg)


class FileOperationError(BoilerplatesError):
    """Raised when file operations fail."""

    pass


class RenderError(BoilerplatesError):
    """Raised when rendering operations fail."""

    pass


class YAMLParseError(BoilerplatesError):
    """Raised when YAML parsing fails."""

    def __init__(self, file_path: str, original_error: Exception):
        self.file_path = file_path
        self.original_error = original_error
        msg = f"Failed to parse YAML file '{file_path}': {original_error}"
        super().__init__(msg)
