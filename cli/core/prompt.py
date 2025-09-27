from __future__ import annotations

from typing import Dict, Any, List, Callable
import logging
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table

from .variables import Variable, VariableCollection

logger = logging.getLogger(__name__)


# ---------------------------
# SECTION: PromptHandler Class
# ---------------------------

class PromptHandler:
  """Simple interactive prompt handler for collecting template variables."""

  def __init__(self) -> None:
    self.console = Console()

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
    for section_key, section in variables._set.items():
      if not section.variables:
        continue

      # Always show section header first
      self.console.print(f"\n[bold cyan]{section.title}[/bold cyan]")
      if section.description:
        self.console.print(f"[dim]{section.description}[/dim]")
      self.console.print("─" * 40, style="dim")

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
        new_value = self._prompt_variable(variable)
        
        if new_value != current_value:
          collected[var_name] = new_value
          variable.value = new_value

    logger.info(f"Variable collection completed. Collected {len(collected)} values")
    return collected

  # !SECTION

  # ---------------------------
  # SECTION: Private Methods
  # ---------------------------

  def _prompt_variable(self, variable: Variable) -> Any:
    """Prompt for a single variable value based on its type."""
    logger.debug(f"Prompting for variable '{variable.name}' (type: {variable.type})")

    prompt_text = variable.prompt or variable.description or variable.name

    # Friendly hint for common semantic types
    if variable.type in ["hostname", "email", "url"]:
      prompt_text += f" ({variable.type})"

    try:
      default_value = variable.get_typed_value()
    except ValueError:
      default_value = variable.value

    handler = self._get_prompt_handler(variable)

    while True:
      try:
        raw = handler(prompt_text, default_value)
        return variable.convert(raw)
      except ValueError as exc:
        self._show_validation_error(str(exc))
      except Exception as e:
        logger.error(f"Error prompting for variable '{variable.name}': {str(e)}")
        default_value = variable.value
        handler = self._get_prompt_handler(variable)

  def _get_prompt_handler(self, variable: Variable) -> Callable:
    """Return the prompt function for a variable type."""
    handlers = {
      "bool": self._prompt_bool,
      "int": self._prompt_int,
      "enum": lambda text, default: self._prompt_enum(text, variable.options or [], default),
    }
    return handlers.get(variable.type, self._prompt_string)

  def _show_validation_error(self, message: str) -> None:
    """Display validation feedback consistently."""
    self.console.print(f"[red]{message}[/red]")

  def _prompt_string(self, prompt_text: str, default: Any = None) -> str:
    value = Prompt.ask(
      prompt_text,
      default=str(default) if default is not None else "",
      show_default=True,
    )
    return value.strip() if value else ""

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

  def _prompt_enum(self, prompt_text: str, options: list[str], default: Any = None) -> str:
    """Prompt for enum selection with validation."""
    if not options:
      return self._prompt_string(prompt_text, default)

    self.console.print(f"  Options: {', '.join(options)}", style="dim")

    # Validate default is in options
    if default and str(default) not in options:
      default = options[0]

    while True:
      value = Prompt.ask(
        prompt_text,
        default=str(default) if default else options[0],
        show_default=True,
      )
      if value in options:
        return value
      self.console.print(f"[red]Invalid choice. Select from: {', '.join(options)}[/red]")

# !SECTION
