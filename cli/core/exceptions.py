"""Custom exceptions for the boilerplate CLI application."""


class BoilerplateError(Exception):
  """Base exception for all boilerplate-related errors."""
  pass


class TemplateError(BoilerplateError):
  """Base exception for template-related errors."""
  pass


class TemplateNotFoundError(TemplateError):
  """Raised when a template cannot be found."""
  
  def __init__(self, template_id: str, module_name: str = None):
    if module_name:
      message = f"Template '{template_id}' not found in module '{module_name}'"
    else:
      message = f"Template '{template_id}' not found"
    super().__init__(message)
    self.template_id = template_id
    self.module_name = module_name


class InvalidTemplateError(TemplateError):
  """Raised when a template has invalid format or content."""
  
  def __init__(self, template_path: str, reason: str):
    message = f"Invalid template at '{template_path}': {reason}"
    super().__init__(message)
    self.template_path = template_path
    self.reason = reason


class TemplateValidationError(TemplateError):
  """Raised when template validation fails."""
  
  def __init__(self, template_id: str, errors: list):
    message = f"Template '{template_id}' validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
    super().__init__(message)
    self.template_id = template_id
    self.errors = errors


class VariableError(BoilerplateError):
  """Base exception for variable-related errors."""
  pass


class UndefinedVariableError(VariableError):
  """Raised when a template references undefined variables."""
  
  def __init__(self, variable_names: set, template_id: str = None):
    var_list = ", ".join(sorted(variable_names))
    if template_id:
      message = f"Template '{template_id}' references undefined variables: {var_list}"
    else:
      message = f"Undefined variables: {var_list}"
    super().__init__(message)
    self.variable_names = variable_names
    self.template_id = template_id


class LibraryError(BoilerplateError):
  """Base exception for library-related errors."""
  pass


class RemoteLibraryError(LibraryError):
  """Raised when operations on remote libraries fail."""
  
  def __init__(self, library_name: str, operation: str, reason: str):
    message = f"Remote library '{library_name}' {operation} failed: {reason}"
    super().__init__(message)
    self.library_name = library_name
    self.operation = operation
    self.reason = reason


class ConfigurationError(BoilerplateError):
  """Raised when configuration is invalid or missing."""
  
  def __init__(self, config_item: str, reason: str):
    message = f"Configuration error for '{config_item}': {reason}"
    super().__init__(message)
    self.config_item = config_item
    self.reason = reason
