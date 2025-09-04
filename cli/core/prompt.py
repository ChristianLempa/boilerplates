from typing import Dict, Any, List, Optional, Union
import logging
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich import box
import re

logger = logging.getLogger('boilerplates')

class PromptHandler:
  """Advanced prompt handler with Rich UI for complex variable group logic."""

  def __init__(self, variable_groups: Dict[str, Any], resolved_defaults: Dict[str, Any] = None):
    """Initialize the prompt handler.
    
    Args:
        variable_groups: Dictionary of variable groups from VariableManager
        resolved_defaults: Pre-resolved default values with priority handling
    """
    self.variable_groups = variable_groups
    self.resolved_defaults = resolved_defaults or {}
    self.console = Console()
    self.final_values = {}
    
  def __call__(self) -> Dict[str, Any]:
    """Execute the complex prompting logic and return final variable values."""
    logger.debug(f"Starting advanced prompt handler with {len(self.variable_groups)} variable groups")
    
    self._show_welcome_message()
    
    # Process each variable group with the complex logic
    for group_name, group_data in self.variable_groups.items():
      self._process_variable_group(group_name, group_data)
    
    self._show_summary()
    return self.final_values
  
  def _show_welcome_message(self):
    """Display a welcome message for the template generation."""
    welcome_text = Text("🚀 Template Generation", style="bold blue")
    subtitle = Text("Configure variables for your template", style="dim")
    
    panel = Panel(
      f"{welcome_text}\n{subtitle}",
      box=box.ROUNDED,
      padding=(1, 2)
    )
    self.console.print(panel)
    self.console.print()
  
  def _process_variable_group(self, group_name: str, group_data: Dict[str, Any]):
    """Process a single variable group with complex prompting logic.
    
    Logic flow:
    1. Check if group has variables with no default values → always prompt
    2. If group is not enabled → ask user if they want to enable it
    3. If group is enabled → prompt for variables without values
    4. Ask if user wants to change existing variable values
    """
    logger.debug(f"Processing variable group: {group_name}")
    
    variables = group_data.get('vars', {})
    if not variables:
      logger.debug(f"Group {group_name} has no variables, skipping")
      return
      
    # Show group header
    self._show_group_header(group_name, group_data.get('description', ''))
    
    # Step 1: Check for variables with no default values (always prompt)
    vars_without_defaults = self._get_variables_without_defaults(variables)
    
    # Step 2: Determine if group should be enabled
    group_enabled = self._determine_group_enabled_status(group_name, variables, vars_without_defaults)
    
    # Always set default values for variables in this group, even if user doesn't want to configure them
    vars_with_defaults = self._get_variables_with_defaults(variables)
    for var_name in vars_with_defaults:
      default_value = self.resolved_defaults.get(var_name)
      self.final_values[var_name] = default_value
    
    if not group_enabled:
      logger.debug(f"Group {group_name} disabled by user, but defaults have been applied")
      return
      
    # Step 3: Prompt for required variables (those without defaults)
    if vars_without_defaults:
      self.console.print(f"[bold red]Required variables for {group_name}:[/bold red]")
      for var_name in vars_without_defaults:
        var_data = variables[var_name]
        value = self._prompt_for_variable(var_name, var_data, required=True)
        self.final_values[var_name] = value
    
    # Step 4: Handle variables with defaults - ask if user wants to change them
    vars_with_defaults = self._get_variables_with_defaults(variables)
    
    if vars_with_defaults:
      self._handle_variables_with_defaults(group_name, vars_with_defaults, variables)
    
    self.console.print()  # Add spacing between groups
  
  def _show_group_header(self, group_name: str, description: str):
    """Display a header for the variable group."""
    header = f"[bold cyan]📦 {group_name.title()} Variables[/bold cyan]"
    if description:
      header += f"\n[dim]{description}[/dim]"
    
    self.console.print(Panel(header, box=box.SIMPLE, padding=(0, 1)))
  
  def _get_variables_without_defaults(self, variables: Dict[str, Any]) -> List[str]:
    """Get list of variable names that have no default values."""
    return [
      var_name for var_name, var_data in variables.items()
      if var_name not in self.resolved_defaults or self.resolved_defaults[var_name] is None
    ]
  
  def _get_variables_with_defaults(self, variables: Dict[str, Any]) -> List[str]:
    """Get list of variable names that have default values."""
    return [
      var_name for var_name, var_data in variables.items()
      if var_name in self.resolved_defaults and self.resolved_defaults[var_name] is not None
    ]
  
  def _determine_group_enabled_status(self, group_name: str, variables: Dict[str, Any], vars_without_defaults: List[str]) -> bool:
    """Determine if a variable group should be enabled based on complex logic."""
    
    # If there are required variables (no defaults), group must be enabled
    if vars_without_defaults:
      logger.debug(f"Group {group_name} has required variables, enabling automatically")
      return True
    
    # Check if group is enabled by default values or should ask user
    vars_with_defaults = self._get_variables_with_defaults(variables)
    if not vars_with_defaults:
      logger.debug(f"Group {group_name} has no variables with defaults, skipping")
      return False
    
    # Show preview of what this group would configure
    self._show_group_preview(group_name, vars_with_defaults)
    
    # Ask user if they want to enable this optional group
    try:
      return Confirm.ask(
        f"[yellow]Do you want to configure {group_name} variables?[/yellow]",
        default=False
      )
    except (EOFError, KeyboardInterrupt):
      logger.debug(f"User interrupted prompt for group {group_name}, defaulting to disabled")
      return False
  
  def _show_group_preview(self, group_name: str, vars_with_defaults: List[str]):
    """Show a preview of variables that would be configured in this group."""
    if not vars_with_defaults:
      return
      
    table = Table(title=f"Variables in {group_name}", box=box.SIMPLE)
    table.add_column("Variable", style="cyan")
    table.add_column("Default Value", style="green")
    
    for var_name in vars_with_defaults:
      default_value = self.resolved_defaults.get(var_name, "None")
      table.add_row(var_name, str(default_value))
    
    self.console.print(table)
  
  def _handle_variables_with_defaults(self, group_name: str, vars_with_defaults: List[str], variables: Dict[str, Any]):
    """Handle variables that have default values."""
    
    # Ask if user wants to customize any of these values (defaults already set earlier)
    try:
      want_to_customize = Confirm.ask(f"[yellow]Do you want to customize any {group_name} variables?[/yellow]", default=False)
    except (EOFError, KeyboardInterrupt):
      logger.debug(f"User interrupted customization prompt for group {group_name}, using defaults")
      return
    
    if want_to_customize:
      for var_name in vars_with_defaults:
        var_data = variables[var_name]
        current_value = self.final_values[var_name]
        
        self.console.print(f"\n[dim]Current value for [bold]{var_name}[/bold]: {current_value}[/dim]")
        
        try:
          change_variable = Confirm.ask(f"Change [bold]{var_name}[/bold]?", default=False)
        except (EOFError, KeyboardInterrupt):
          logger.debug(f"User interrupted change prompt for variable {var_name}, keeping current value")
          continue
          
        if change_variable:
          new_value = self._prompt_for_variable(var_name, var_data, required=False, current_value=current_value)
          self.final_values[var_name] = new_value
  
  def _prompt_for_variable(self, var_name: str, var_data: Dict[str, Any], required: bool = False, current_value: Any = None) -> Any:
    """Prompt user for a single variable with type validation."""
    
    var_type = var_data.get('type', 'string')
    description = var_data.get('description', '')
    options = var_data.get('options', [])
    
    # Build prompt message
    prompt_parts = [f"[bold]{var_name}[/bold]"]
    if description:
      prompt_parts.append(f"({description})")
    
    prompt_message = " ".join(prompt_parts)
    
    # Add type information if not string
    if var_type != 'string':
      prompt_message += f" [dim]({var_type})[/dim]"
    
    # Handle different variable types
    try:
      if var_type == 'boolean':
        return self._prompt_boolean(prompt_message, current_value)
      elif var_type == 'integer':
        return self._prompt_integer(prompt_message, current_value)
      elif var_type == 'float':
        return self._prompt_float(prompt_message, current_value)
      elif var_type == 'choice' and options:
        return self._prompt_choice(prompt_message, options, current_value)
      elif var_type == 'list':
        return self._prompt_list(prompt_message, current_value)
      else:  # string or unknown type
        return self._prompt_string(prompt_message, current_value, required)
        
    except KeyboardInterrupt:
      self.console.print("\n[red]Operation cancelled by user[/red]")
      raise
    except Exception as e:
      logger.error(f"Error prompting for variable {var_name}: {e}")
      self.console.print(f"[red]Error getting input for {var_name}. Using default string prompt.[/red]")
      return self._prompt_string(prompt_message, current_value, required)
  
  def _prompt_string(self, prompt_message: str, current_value: Any = None, required: bool = False) -> str:
    """Prompt for string input with validation."""
    default_val = str(current_value) if current_value is not None else None
    
    while True:
      try:
        value = Prompt.ask(prompt_message, default=default_val)
        
        if required and not value.strip():
          self.console.print("[red]This field is required and cannot be empty[/red]")
          continue
          
        return value.strip()
      except (EOFError, KeyboardInterrupt):
        if required:
          self.console.print(f"\n[red]This field is required. Using empty string.[/red]")
          return ""
        else:
          return default_val or ""
  
  def _prompt_boolean(self, prompt_message: str, current_value: Any = None) -> bool:
    """Prompt for boolean input."""
    default_val = bool(current_value) if current_value is not None else None
    try:
      return Confirm.ask(prompt_message, default=default_val)
    except (EOFError, KeyboardInterrupt):
      return default_val if default_val is not None else False
  
  def _prompt_integer(self, prompt_message: str, current_value: Any = None) -> int:
    """Prompt for integer input with validation."""
    default_val = int(current_value) if current_value is not None else None
    
    while True:
      try:
        return IntPrompt.ask(prompt_message, default=default_val)
      except ValueError:
        self.console.print("[red]Please enter a valid integer[/red]")
      except (EOFError, KeyboardInterrupt):
        return default_val if default_val is not None else 0
  
  def _prompt_float(self, prompt_message: str, current_value: Any = None) -> float:
    """Prompt for float input with validation."""
    default_val = float(current_value) if current_value is not None else None
    
    while True:
      try:
        return FloatPrompt.ask(prompt_message, default=default_val)
      except ValueError:
        self.console.print("[red]Please enter a valid number[/red]")
      except (EOFError, KeyboardInterrupt):
        return default_val if default_val is not None else 0.0
  
  def _prompt_choice(self, prompt_message: str, options: List[Any], current_value: Any = None) -> Any:
    """Prompt for choice from a list of options."""
    
    # Show available options
    self.console.print(f"\n[dim]Available options:[/dim]")
    for i, option in enumerate(options, 1):
      marker = "→" if option == current_value else " "
      self.console.print(f"  {marker} {i}. {option}")
    
    while True:
      try:
        choice = Prompt.ask(f"{prompt_message} (1-{len(options)})")
        
        try:
          choice_idx = int(choice) - 1
          if 0 <= choice_idx < len(options):
            return options[choice_idx]
          else:
            self.console.print(f"[red]Please enter a number between 1 and {len(options)}[/red]")
        except ValueError:
          # Try to match by string value
          matching_options = [opt for opt in options if str(opt).lower() == choice.lower()]
          if matching_options:
            return matching_options[0]
          self.console.print(f"[red]Please enter a valid option number (1-{len(options)}) or exact option name[/red]")
      except (EOFError, KeyboardInterrupt):
        return current_value if current_value is not None else options[0] if options else None
  
  def _prompt_list(self, prompt_message: str, current_value: Any = None) -> List[str]:
    """Prompt for list input (comma-separated values)."""
    
    current_str = ""
    if current_value and isinstance(current_value, list):
      current_str = ", ".join(str(item) for item in current_value)
    elif current_value:
      current_str = str(current_value)
    
    self.console.print(f"[dim]Enter values separated by commas[/dim]")
    
    try:
      value = Prompt.ask(prompt_message, default=current_str)
      
      if not value.strip():
        return []
      
      # Split by comma and clean up
      items = [item.strip() for item in value.split(',') if item.strip()]
      return items
    except (EOFError, KeyboardInterrupt):
      if current_value and isinstance(current_value, list):
        return current_value
      elif current_value:
        return [str(current_value)]
      else:
        return []
  
  def _show_summary(self):
    """Display a summary of all configured variables."""
    if not self.final_values:
      self.console.print("[yellow]No variables were configured.[/yellow]")
      return
    
    self.console.print("\n" + "="*50)
    self.console.print("[bold green]📋 Configuration Summary[/bold green]")
    self.console.print("="*50)
    
    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("Variable", style="cyan", min_width=20)
    table.add_column("Value", style="green")
    table.add_column("Type", style="dim")
    
    for var_name, value in self.final_values.items():
      var_type = type(value).__name__
      # Format value for display
      if isinstance(value, list):
        display_value = ", ".join(str(item) for item in value)
      else:
        display_value = str(value)
      
      table.add_row(var_name, display_value, var_type)
    
    self.console.print(table)
    self.console.print()
    
    try:
      if not Confirm.ask("[bold]Proceed with template generation?[/bold]", default=True):
        raise KeyboardInterrupt("Template generation cancelled by user")
    except (EOFError, KeyboardInterrupt):
      # If user cancels, still proceed with defaults
      self.console.print("[yellow]Using current configuration to proceed.[/yellow]")
