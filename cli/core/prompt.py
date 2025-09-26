from typing import Dict, Any, List, Optional
from collections import OrderedDict
import logging
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table

from .variables import Variable, VariableCollection
from .renderers import render_variable_table

logger = logging.getLogger(__name__)


class PromptHandler:
  """Interactive prompt handler for collecting template variables.

  Simplified design:
  - Single entrypoint: collect_variables(VariableCollection)
  - Asks only for variables that don't have values
  - Clear, compact output with a summary table
  """

  def __init__(self):
    self.console = Console()

  def collect_variables(
    self,
    variables: VariableCollection,
    template_name: str = "",
    module_name: str = "",
    template_var_order: List[str] = None,
    module_var_order: List[str] = None,
    sections: Optional[OrderedDict[str, Dict[str, Any]]] = None,
  ) -> Dict[str, Any]:
    """Collect values for variables that need input with an ordered, sectioned flow.

    When sections metadata is provided, it defines the order, prompt text, and
    toggle behavior for each section. Otherwise all variables are shown in a
    single "General" group.
    """
    template_var_order = template_var_order or []
    module_var_order = module_var_order or []

    section_meta_list: List[Dict[str, Any]] = []
    if sections:
      section_meta_list = list(sections.values())
    else:
      section_meta_list = [
        {
          "title": "General",
          "variables": variables.get_variable_names(),
          "toggle": None,
          "prompt": None,
          "description": None,
        }
      ]

    self._display_current_values(variables, sections)

    if not Confirm.ask("Customize any settings?", default=False):
      logger.info("User opted to keep all default values")
      return {}

    collected: Dict[str, Any] = {}

    for section_meta in section_meta_list:
      title = section_meta.get("title") or "General"
      prompt_text = section_meta.get("prompt")
      toggle_name = section_meta.get("toggle")
      description_text = section_meta.get("description")
      var_names = section_meta.get("variables", [])

      # Filter to existing variables
      variable_objects = [variables.get_variable(name) for name in var_names]
      variable_objects = [var for var in variable_objects if var is not None]

      if not variable_objects:
        continue

      toggle_var = None
      if toggle_name:
        toggle_var = variables.get_variable(toggle_name)
        if toggle_var is None:
          toggle_var = next((var for var in variable_objects if var.name == toggle_name), None)

      if toggle_var:
        enabled = self._prompt_bool(
          prompt_text or f"Enable {title}?",
          toggle_var.get_typed_value(),
        )
        if enabled != bool(toggle_var.get_typed_value()):
          collected[toggle_var.name] = enabled
          toggle_var.value = enabled
        if not enabled:
          continue
      elif prompt_text:
        self.console.print(prompt_text, style="dim")

      self.console.print(f"[bold magenta]{title}[/bold magenta]")
      self.console.print("─" * 50, style="dim")
      if description_text:
        self.console.print(f"[dim]{description_text}[/dim]")

      for var in variable_objects:
        if toggle_var and var.name == toggle_var.name:
          continue
        current = var.get_typed_value()
        new_value = self._prompt_variable(var)
        if new_value != current:
          collected[var.name] = new_value
          var.value = new_value

      self.console.print()

    logger.info(f"Variable collection completed. Collected {len(collected)} values")
    return collected

  def _display_current_values(
    self,
    variables: VariableCollection,
    sections: Optional[OrderedDict[str, Dict[str, Any]]] = None,
  ) -> None:
    self.console.print(
      render_variable_table(variables, title="Current Defaults", sections=sections)
    )


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

  def _get_prompt_handler(self, variable: Variable):
    """Return the prompt function for a variable type."""
    if variable.type == "enum":
      return lambda text, default: self._prompt_enum(text, variable.options or [], default)
    return {
      "bool": self._prompt_bool,
      "int": self._prompt_int,
    }.get(variable.type, self._prompt_string)

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

  def _prompt_enum(self, prompt_text: str, options: List[str], default: Any = None) -> str:
    if not options:
      logger.warning("Enum variable has no options, falling back to string prompt")
      return self._prompt_string(prompt_text, default)

    self.console.print(f"  Options: {', '.join(options)}", style="dim")

    if default and default not in options:
      logger.warning(f"Default value '{default}' not in options {options}")
      default = None

    while True:
      value = Prompt.ask(
        prompt_text,
        default=str(default) if default else options[0],
        show_default=True,
      )
      if value in options:
        return value
      self.console.print(f"  [red]Invalid choice. Please select from: {', '.join(options)}[/red]")

  def display_variable_summary(self, collected_values: Dict[str, Any], template_name: str = ""):
    """Display a summary of collected variable values."""
    if not collected_values:
      return

    title = "Variable Summary"
    if template_name:
      title += f" - {template_name}"

    table = Table(title=title, show_header=True, header_style="bold blue")
    table.add_column("Variable", style="cyan", min_width=20)
    table.add_column("Value", style="green")
    table.add_column("Type", style="dim", justify="center")

    for var_name in sorted(collected_values.keys()):
      value = collected_values[var_name]
      if isinstance(value, bool):
        display_value = "true" if value else "false"  # No emojis per logging rules
        var_type = "bool"
      elif isinstance(value, int):
        display_value = str(value)
        var_type = "int"
      else:
        display_value = str(value) if value else ""
        var_type = "str"

      if len(display_value) > 50:
        display_value = display_value[:47] + "..."

      table.add_row(var_name, display_value, var_type)

    self.console.print()
    self.console.print(table)
    self.console.print()
