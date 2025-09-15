from typing import Dict, Any, List
import logging
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .variables import Variable, VariableCollection

logger = logging.getLogger(__name__)
console = Console()


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
  ) -> Dict[str, Any]:
    """Collect values for variables that need input with an ordered, sectioned flow.

    Sections (in order):
    1) General (always)
    2) <Template Name> Specific (always) - variables defined in frontmatter
    3) Each *_enabled section (ask to enable -> then prompt variables)
    """
    template_var_order = template_var_order or []
    module_var_order = module_var_order or []

    # Build lookup maps for easy access and ordering
    vars_map = variables.variables

    # Partition variables
    toggles: Dict[str, Variable] = {}
    section_vars: Dict[str, List[Variable]] = {}
    general_vars: List[Variable] = []
    template_specific_vars: List[Variable] = []

    # Determine which names are template-specific by provided order
    template_specific_names = set(template_var_order)

    for name, var in vars_map.items():
      # Classify template-specific first
      if name in template_specific_names:
        template_specific_vars.append(var)
        continue

      # Identify section toggles by *_enabled convention
      if name.endswith("_enabled") and var.type == "bool":
        section = name[: -len("_enabled")]
        toggles[section] = var
        section_vars.setdefault(section, [])
        continue

      # If it begins with a section prefix, associate with that section
      prefix = name.split("_", 1)[0]
      if prefix in toggles:
        section_vars.setdefault(prefix, []).append(var)
      else:
        general_vars.append(var)

    # Helper: compute which need values
    def needs_value(v: Variable) -> bool:
      return v.value is None or v.value == ""

    # Order preservation based on source order lists
    def order_by(names: List[str], items: List[Variable]) -> List[Variable]:
      order_index = {n: i for i, n in enumerate(names)}
      return sorted(items, key=lambda v: order_index.get(v.name, 1_000_000))

    general_needing = [v for v in general_vars if needs_value(v)]
    template_needing = [v for v in template_specific_vars if needs_value(v)]
    sections_needing = {s: [v for v in section_vars.get(s, []) if needs_value(v)] for s in section_vars.keys()}

    # Count for header
    total_needed = len(general_needing) + len(template_needing) + sum(len(lst) for lst in sections_needing.values())

    collected: Dict[str, Any] = {}

    # General (always)
    general_needing = order_by(module_var_order, general_needing)
    if general_needing:
      self.console.print("[bold magenta]General Configuration[/bold magenta]")
      self.console.print("─" * 50, style="dim")
      # Required first (no default)
      for var in [v for v in general_needing if needs_value(v)]:
        collected[var.name] = self._prompt_required(var)
      # Show current values (non-empty), ask if user wants to change
      current = [v for v in general_vars if not needs_value(v)]
      self._maybe_reconfigure(current, collected)
      self.console.print()

    # Template-specific (always)
    template_needing = order_by(template_var_order, template_needing)
    if template_specific_vars:
      self.console.print(f"[bold magenta]{template_name} Specific[/bold magenta]")
      self.console.print("─" * 50, style="dim")
      # Warning on overrides
      for v in template_specific_vars:
        if v.name in module_var_order:
          self.console.print(f"[yellow]Warning:[/yellow] Template Specific variable '{v.name}' is also defined by {module_name}; template value takes precedence.")
      # Required first
      for var in [v for v in template_needing if needs_value(v)]:
        collected[var.name] = self._prompt_required(var)
      # Reconfigure current values
      current = [v for v in template_specific_vars if not needs_value(v)]
      self._maybe_reconfigure(current, collected)
      self.console.print()

    # Toggle sections in declaration order
    for section in toggles.keys():
      toggle_var = toggles[section]
      # Ask to enable (general/template are always-on)
      enabled = self._prompt_bool(f"Enable {section.replace('_', ' ').title()}?", toggle_var.get_typed_value())
      collected[toggle_var.name] = enabled
      if not enabled:
        continue

      # Required first
      needing = order_by(module_var_order, sections_needing.get(section, []))
      if needing or section_vars.get(section):
        self.console.print(f"[bold magenta]{section.replace('_', ' ').title()} Configuration[/bold magenta]")
        self.console.print("─" * 50, style="dim")
        for var in [v for v in needing if needs_value(v)]:
          collected[var.name] = self._prompt_required(var)
        # Reconfigure
        current = [v for v in section_vars.get(section, []) if not needs_value(v)]
        self._maybe_reconfigure(current, collected)
        self.console.print()

    logger.info(f"Variable collection completed. Collected {len(collected)} values")
    return collected

  def _prompt_required(self, variable: Variable) -> Any:
    """Prompt for a required variable; empty answers are not allowed."""
    while True:
      val = self._prompt_variable(variable)
      if val is None or (isinstance(val, str) and val.strip() == ""):
        self.console.print("[red]This field is required. Please enter a value.[/red]")
        continue
      return val

  def _maybe_reconfigure(self, variables: List[Variable], collected: Dict[str, Any]):
    """Show current values inline and ask if user wants to change them; if yes, prompt with defaults."""
    vars_with_values = [(v.name, v.get_typed_value()) for v in variables]
    if not vars_with_values:
      return

    # Build concise single-line presentation: Current Values: var=value, var2=value
    line = Text()
    line.append("Current Values: ", style="white")
    for idx, (name, value) in enumerate(vars_with_values):
      if idx > 0:
        line.append(", ", style="white")
      line.append(name, style="cyan")
      line.append("=", style="white")
      display = str(value) if value is not None else ""
      line.append(display, style="green")
    self.console.print(line)

    if Confirm.ask("Change any of these values?", default=False):
      for v in variables:
        default_before = v.value
        new_val = self._prompt_variable(v)
        # If user pressed enter with empty string for str type, keep previous
        if new_val == "" and isinstance(default_before, str):
          continue
        collected[v.name] = new_val


  def _prompt_variable(self, variable: Variable) -> Any:
    """Prompt for a single variable value based on its type."""
    logger.debug(f"Prompting for variable '{variable.name}' (type: {variable.type})")

    prompt_text = variable.prompt or variable.description or variable.name

    # Friendly hint for common semantic types
    if variable.type in ["hostname", "email", "url"]:
      prompt_text += f" ({variable.type})"

    # Show default value if available
    default_value = variable.value

    try:
      if variable.type == "bool":
        return self._prompt_bool(prompt_text, default_value)
      if variable.type == "int":
        return self._prompt_int(prompt_text, default_value)
      if variable.type == "enum":
        return self._prompt_enum(prompt_text, variable.options or [], default_value)
      return self._prompt_string(prompt_text, default_value)
    except Exception as e:
      logger.error(f"Error prompting for variable '{variable.name}': {str(e)}")
      return self._prompt_string(prompt_text, default_value)

  def _prompt_string(self, prompt_text: str, default: Any = None) -> str:
    value = Prompt.ask(
      prompt_text,
      default=str(default) if default is not None else "",
      show_default=False,
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
        show_default=False,
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

# TODO: Add validation hooks (URL, email, hostname) if needed
# NOTE: Keep prompts single-line, clean, and with proper log levels per rules
