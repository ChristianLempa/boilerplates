"""Custom exception classes for the boilerplates CLI.

This module defines specific exception types for better error handling
and diagnostics throughout the application.
"""

from typing import Optional, List, Dict


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
    
    def __init__(self, template_id: str, module_name: Optional[str] = None):
        self.template_id = template_id
        self.module_name = module_name
        msg = f"Template '{template_id}' not found"
        if module_name:
            msg += f" in module '{module_name}'"
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
    
    def __init__(self, template_id: str, errors: List[str]):
        self.template_id = template_id
        self.errors = errors
        msg = f"Jinja2 syntax errors in template '{template_id}':\n" + "\n".join(errors)
        super().__init__(msg)


class TemplateValidationError(TemplateError):
    """Raised when template validation fails."""
    pass


class TemplateRenderError(TemplateError):
    """Raised when template rendering fails."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column: Optional[int] = None,
        context_lines: Optional[List[str]] = None,
        variable_context: Optional[Dict[str, str]] = None,
        suggestions: Optional[List[str]] = None,
        original_error: Optional[Exception] = None
    ):
        self.file_path = file_path
        self.line_number = line_number
        self.column = column
        self.context_lines = context_lines or []
        self.variable_context = variable_context or {}
        self.suggestions = suggestions or []
        self.original_error = original_error
        
        # Build enhanced error message
        parts = [message]
        
        if file_path:
            location = f"File: {file_path}"
            if line_number:
                location += f", Line: {line_number}"
                if column:
                    location += f", Column: {column}"
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
