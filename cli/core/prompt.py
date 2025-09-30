from __future__ import annotations

from typing import Dict, Any, List, Callable
import logging
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table

from .display import DisplayManager
from .variables import Variable, VariableCollection

logger = logging.getLogger(__name__)


# ---------------------------
# SECTION: PromptHandler Class
# ---------------------------

class PromptHandler:
  """Simple interactive prompt handler for collecting template variables."""

  def __init__(self) -> None:
    self.console = Console()
    self.display = DisplayManager()

  # --------------------------
  # SECTION: Public Methods
  # --------------------------

  def collect_variables(self, variables: VariableCollection) -> dict[str, Any]:
    """Collect values for variables by iterating through sections.
    
    Args:
        variables: VariableCollection with organized sections and variables
        
    Returns:
        Dict of variable names to collected values
    """
    if not Confirm.ask("Customize any settings?", default=False):
      logger.info("User opted to keep all default values")
      return {}

    collected: Dict[str, Any] = {}

    # Process each section
    for section_key, section in variables.get_sections().items():
      if not section.variables:
        continue

      # Always show section header first
      self.display.display_section_header(section.title, section.description)

      # Handle section toggle - skip for required sections
      if section.required:
        # Required sections are always processed, no toggle prompt needed
        logger.debug(f"Processing required section '{section.key}' without toggle prompt")
      elif section.toggle:
        toggle_var = section.variables.get(section.toggle)
        if toggle_var:
          prompt_text = section.prompt or f"Enable {section.title}?"
          current_value = toggle_var.get_typed_value()
          new_value = self._prompt_bool(prompt_text, current_value)
          
          if new_value != current_value:
            collected[toggle_var.name] = new_value
            toggle_var.value = new_value
          
          # Skip remaining variables in section if disabled
          if not new_value:
            continue

      # Collect variables in this section
      for var_name, variable in section.variables.items():
        # Skip toggle variable (already handled)
        if section.toggle and var_name == section.toggle:
          continue
          
        current_value = variable.get_typed_value()
        # Pass section.required so _prompt_variable can enforce required inputs
        new_value = self._prompt_variable(variable, required=section.required)
        
        if new_value != current_value:
          collected[var_name] = new_value
          variable.value = new_value

    logger.info(f"Variable collection completed. Collected {len(collected)} values")
    return collected

  # !SECTION

  # ---------------------------
  # SECTION: Private Methods
  # ---------------------------

  def _prompt_variable(self, variable: Variable, required: bool = False) -> Any:
    """Prompt for a single variable value based on its type."""
    logger.debug(f"Prompting for variable '{variable.name}' (type: {variable.type})")
    prompt_text = variable.prompt or variable.description or variable.name

    # Normalize default value once and reuse. This centralizes handling for
    # enums, bools, ints and strings and avoids duplicated fallback logic.
    default_value = self._normalize_default(variable)

    # Friendly hint for common semantic types — only show if a default exists
    if default_value is not None and variable.type in ["hostname", "email", "url"]:
      prompt_text += f" ({variable.type})"

    # If variable is required and there's no default, mark it in the prompt
    if required and default_value is None:
      prompt_text = f"{prompt_text} [bold red]*required[/bold red]"

    handler = self._get_prompt_handler(variable)

    # Attach the optional 'extra' explanation inline (dimmed) so it appears
    # after the main question rather than before it.
    if getattr(variable, 'extra', None):
      # Put the extra hint inline (same line) instead of on the next line.
      prompt_text = f"{prompt_text} [dim]{variable.extra}[/dim]"

    while True:
      try:
        raw = handler(prompt_text, default_value)
        # Convert/validate the user's input using the Variable conversion
        converted = variable.convert(raw)

        # If this variable is required, do not accept None/empty values
        if required and (converted is None or (isinstance(converted, str) and converted == "")):
          raise ValueError("value cannot be empty for required variable")

        # Return the converted value (caller will update variable.value)
        return converted
      except ValueError as exc:
        # Conversion/validation failed — show a consistent error message and retry
        self._show_validation_error(str(exc))
      except Exception as e:
        # Unexpected error — log and retry using the stored (unconverted) value
        logger.error(f"Error prompting for variable '{variable.name}': {str(e)}")
        default_value = variable.value
        handler = self._get_prompt_handler(variable)

  def _normalize_default(self, variable: Variable) -> Any:
    """Return a normalized default suitable for prompt handlers.

    Tries to use the typed value if available, otherwise falls back to the raw
    stored value. For enums, ensures the default is one of the options.
    """
    try:
      typed = variable.get_typed_value()
    except Exception:
      typed = variable.value

    # Special-case enums: ensure default is valid
    if variable.type == "enum":
      options = variable.options or []
      if not options:
        return typed
      # If typed is falsy or not in options, pick first option as fallback
      if typed is None or str(typed) not in options:
        return options[0]
      return str(typed)

    # For booleans and ints return as-is (handlers will accept these types)
    if variable.type == "bool":
      if isinstance(typed, bool):
        return typed
      if typed is None:
        return None
      return bool(typed)

    if variable.type == "int":
      try:
        return int(typed) if typed is not None and typed != "" else None
      except Exception:
        return None

    # Default: return string or None
    if typed is None:
      return None
    return str(typed)

  def _get_prompt_handler(self, variable: Variable) -> Callable:
    """Return the prompt function for a variable type."""
    handlers = {
      "bool": self._prompt_bool,
      "int": self._prompt_int,
      # For enum prompts we pass the variable.extra through so options and extra
      # can be combined into a single inline hint.
      "enum": lambda text, default: self._prompt_enum(text, variable.options or [], default, extra=getattr(variable, 'extra', None)),
    }
    return handlers.get(variable.type, lambda text, default: self._prompt_string(text, default, is_sensitive=variable.sensitive))

  def _show_validation_error(self, message: str) -> None:
    """Display validation feedback consistently."""
    self.display.display_validation_error(message)

  def _prompt_string(self, prompt_text: str, default: Any = None, is_sensitive: bool = False) -> str:
    value = Prompt.ask(
      prompt_text,
      default=str(default) if default is not None else "",
      show_default=True,
      password=is_sensitive
    )
    if value is None:
      return None
    stripped = value.strip()
    return stripped if stripped != "" else None

  def _prompt_bool(self, prompt_text: str, default: Any = None) -> bool:
    default_bool = None
    if default is not None:
      default_bool = default if isinstance(default, bool) else str(default).lower() in ("true", "1", "yes", "on")
    return Confirm.ask(prompt_text, default=default_bool)

  def _prompt_int(self, prompt_text: str, default: Any = None) -> int:
    default_int = None
    if default is not None:
      try:
        default_int = int(default)
      except (ValueError, TypeError):
        logger.warning(f"Invalid default integer value: {default}")
    return IntPrompt.ask(prompt_text, default=default_int)

  def _prompt_enum(self, prompt_text: str, options: list[str], default: Any = None, extra: str | None = None) -> str:
    """Prompt for enum selection with validation. """
    if not options:
      return self._prompt_string(prompt_text, default)

    # Build a single inline hint that contains both the options and any extra
    # explanation, rendered dimmed and appended to the prompt on one line.
    hint_parts: list[str] = []
    hint_parts.append(f"Options: {', '.join(options)}")
    if extra:
      hint_parts.append(extra)

    # Show options and extra inline (same line) in a single dimmed block.
    options_text = f" [dim]{' — '.join(hint_parts)}[/dim]"
    prompt_text_with_options = prompt_text + options_text

    # Validate default is in options
    if default and str(default) not in options:
      default = options[0]

    while True:
      value = Prompt.ask(
        prompt_text_with_options,
        default=str(default) if default else options[0],
        show_default=True,
      )
      if value in options:
        return value
      self.console.print(f"[red]Invalid choice. Select from: {', '.join(options)}[/red]")

# !SECTION
