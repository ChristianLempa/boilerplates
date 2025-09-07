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

    # Process each variable group with the complex logic
    # Maintain order by processing 'general' group first if it exists
    ordered_groups = []
    if 'general' in self.variable_groups:
      ordered_groups.append(('general', self.variable_groups['general']))
    
    # Add remaining groups in their original order
    for group_name, group_data in self.variable_groups.items():
      if group_name != 'general':
        ordered_groups.append((group_name, group_data))
    
    for group_name, group_data in ordered_groups:
      self._process_variable_group(group_name, group_data)
    
    self._show_summary()
    return self.final_values
  
  def _process_variable_group(self, group_name: str, group_data: Dict[str, Any]):
    """Process a single variable group with complex prompting logic.
    
    Logic flow:
    1. Check if group has variables with no default values → always prompt
    2. If group is not enabled → ask user if they want to enable it
    3. If group is enabled → prompt for variables without values
    4. Ask if user wants to change existing variable values
    """
    
    variables = group_data.get('vars', {})
    if not variables:
      return

    # Show compact group header only if there are variables to configure
    vars_without_defaults = self._get_variables_without_defaults(variables)
    vars_with_defaults = self._get_variables_with_defaults(variables)
    
    # Only show header if we need user interaction  
    if not (vars_without_defaults or vars_with_defaults):
      return
      
    # Use icon from group configuration
    group_icon = group_data.get('icon', '')
    group_display_name = group_data.get('display_name', group_name.title())
    icon_display = f"{group_icon} " if group_icon else ""
    self.console.print(f"\n{icon_display}[bold magenta]{group_display_name} Variables[/bold magenta]")

    # Check if this group has an enabler variable
    enabler_var_name = group_data.get('enabler', '')
    
    # Always set default values for variables in this group
    for var_name in vars_with_defaults:
      default_value = self.resolved_defaults.get(var_name)
      self.final_values[var_name] = default_value
    
    if enabler_var_name and enabler_var_name in variables:
      # For groups with enablers, handle everything in _handle_group_with_enabler
      self._handle_group_with_enabler(group_name, group_data, variables, vars_without_defaults, vars_with_defaults)
    else:
      # Original flow for groups without enablers
      # Step 2: Determine if group should be enabled
      group_enabled = self._determine_group_enabled_status(group_name, group_data, variables, vars_without_defaults)
      
      # When group is not enabled
      if not group_enabled:
        return
        
      # Step 3: Prompt for required variables (those without defaults)
      if vars_without_defaults:
        for var_name in vars_without_defaults:
          var_data = variables[var_name]
          value = self._prompt_for_variable(var_name, var_data, required=True)
          self.final_values[var_name] = value
      
      # Step 4: Handle variables with defaults - ask if user wants to change them
      if vars_with_defaults:
        self._handle_variables_with_defaults(group_name, vars_with_defaults, variables)
    # Groups are now more compact, minimal spacing needed
  
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
  
  def _determine_group_enabled_status(self, group_name: str, group_data: Dict[str, Any], variables: Dict[str, Any], vars_without_defaults: List[str]) -> bool:
    """Determine if a variable group should be enabled based on complex logic."""
    
    # Check if this group has an enabler variable
    enabler_var_name = group_data.get('enabler', '')
    if enabler_var_name and enabler_var_name in variables:
      # This is a group controlled by an enabler variable
      # The enabler variable will be prompted separately
      # For now, assume it's enabled so we can prompt for the enabler
      return True
    
    # If there are required variables (no defaults), group must be enabled
    if vars_without_defaults:
      logger.debug(f"Group {group_name} has required variables, enabling automatically")
      return True
    
    # Check if any variable in the group is marked as required
    has_required_vars = any(var_data.get('required', False) for var_data in variables.values())
    if has_required_vars:
      logger.debug(f"Group {group_name} has variables marked as required, enabling automatically")
      return True
    
    # Check if group is enabled by default values or should ask user
    vars_with_defaults = self._get_variables_with_defaults(variables)
    if not vars_with_defaults:
      logger.debug(f"Group {group_name} has no variables with defaults, skipping")
      return False
    
    # Ask user if they want to enable this optional group
    try:
      enable_group = Confirm.ask(
        f"Do you want to enable [bold]{group_name}[/bold]?",
        default=False
      )
      
      # If group is enabled and has variables with defaults, ask if they want to change values
      if enable_group and vars_with_defaults:
        # This will be handled in the main flow after group is enabled
        pass
        
      return enable_group
    except (EOFError, KeyboardInterrupt):
      # For optional group configuration, gracefully handle interruption
      logger.debug(f"User interrupted prompt for group {group_name}, defaulting to disabled")
      return False
  
  
  def _show_group_preview(self, group_name: str, vars_with_defaults: List[str]):
    """Show configured values in dim white below header."""
    if not vars_with_defaults:
      return
      
    # Create a clean display of configured values
    var_previews = []
    for var_name in vars_with_defaults:
      default_value = self.resolved_defaults.get(var_name, "None")
      # Truncate long values for cleaner display
      display_value = str(default_value)
      if len(display_value) > 25:
        display_value = display_value[:22] + "..."
      var_previews.append(f"{var_name}={display_value}")
    
    # Show configured values in dim white
    vars_text = ", ".join(var_previews)
    self.console.print(f"[dim white]({vars_text})[/dim white]")
  
  def _handle_variables_with_defaults(self, group_name: str, vars_with_defaults: List[str], variables: Dict[str, Any]):
    """Handle variables that have default values."""
    
    # Show preview of current values before asking if user wants to change them
    self._show_group_preview(group_name, vars_with_defaults)
    
    # Ask if user wants to customize any of these values (defaults already set earlier)
    try:
      want_to_customize = Confirm.ask(f"Do you want to change {group_name} values?", default=False)
    except (EOFError, KeyboardInterrupt):
      logger.debug(f"User interrupted customization prompt for group {group_name}, using defaults")
      return
    
    if want_to_customize:
      # Directly prompt for each variable without asking if they want to change it
      for var_name in vars_with_defaults:
        var_data = variables[var_name]
        current_value = self.final_values[var_name]
        
        # Directly prompt for the new value
        new_value = self._prompt_for_variable(var_name, var_data, required=False, current_value=current_value)
        self.final_values[var_name] = new_value
  
  def _prompt_for_variable(self, var_name: str, var_data: Dict[str, Any], required: bool = False, current_value: Any = None) -> Any:
    """Prompt user for a single variable with new format: Enter VARIABLE_NAME (DESCRIPTION) (DEFAULT)."""
    
    var_type = var_data.get('type', 'string')
    description = var_data.get('description', '')
    options = var_data.get('options', [])
    
    # Build new format prompt: Enter VARIABLE_NAME (DESCRIPTION) (DEFAULT_VALUE)
    prompt_parts = ["Enter", f"[bold]{var_name}[/bold]"]
    
    # Add description in parentheses if available
    if description:
      prompt_parts.append(f"({description})")
    
    # Show default value if available
    if current_value is not None:
      prompt_parts.append(f"[dim]({current_value})[/dim]")
    elif required:
      prompt_parts.append("[red](Required)[/red]")
    
    prompt_message = " ".join(prompt_parts)
    
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
      # Let KeyboardInterrupt propagate up to be handled at module level
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
        
        # Handle None values that can occur when user provides no input
        if value is None:
          value = ""
        
        if required and not value.strip():
          self.console.print("[red]This field is required and cannot be empty[/red]")
          continue
          
        return value.strip()
      except (EOFError, KeyboardInterrupt):
        # Let KeyboardInterrupt propagate up for proper cancellation
        raise KeyboardInterrupt("Template generation cancelled by user")
  
  def _prompt_boolean(self, prompt_message: str, current_value: Any = None) -> bool:
    """Prompt for boolean input."""
    default_val = bool(current_value) if current_value is not None else None
    try:
      return Confirm.ask(prompt_message, default=default_val)
    except (EOFError, KeyboardInterrupt):
      raise KeyboardInterrupt("Template generation cancelled by user")
  
  def _prompt_integer(self, prompt_message: str, current_value: Any = None) -> int:
    """Prompt for integer input with validation."""
    default_val = int(current_value) if current_value is not None else None
    
    while True:
      try:
        return IntPrompt.ask(prompt_message, default=default_val)
      except ValueError:
        self.console.print("[red]Please enter a valid integer[/red]")
      except (EOFError, KeyboardInterrupt):
        raise KeyboardInterrupt("Template generation cancelled by user")
  
  def _prompt_float(self, prompt_message: str, current_value: Any = None) -> float:
    """Prompt for float input with validation."""
    default_val = float(current_value) if current_value is not None else None
    
    while True:
      try:
        return FloatPrompt.ask(prompt_message, default=default_val)
      except ValueError:
        self.console.print("[red]Please enter a valid number[/red]")
      except (EOFError, KeyboardInterrupt):
        raise KeyboardInterrupt("Template generation cancelled by user")
  
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
        raise KeyboardInterrupt("Template generation cancelled by user")
  
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
      raise KeyboardInterrupt("Template generation cancelled by user")
  
  def _handle_group_with_enabler(self, group_name: str, group_data: Dict[str, Any], 
                                 variables: Dict[str, Any], vars_without_defaults: List[str], 
                                 vars_with_defaults: List[str]):
    """Handle groups that have an enabler variable."""
    enabler_var_name = group_data.get('enabler', '')
    enabler_var_data = variables.get(enabler_var_name, {})
    current_enabler_value = self.final_values.get(enabler_var_name, False)
    
    # Ask if they want to enable the feature
    try:
      enable_feature = Confirm.ask(
        f"Do you want to enable [bold]{group_name}[/bold]?",
        default=bool(current_enabler_value)
      )
      self.final_values[enabler_var_name] = enable_feature
      
      if not enable_feature:
        # If the feature is disabled, skip all other variables in this group
        return
        
    except (EOFError, KeyboardInterrupt):
      logger.debug(f"User interrupted enabler prompt for group {group_name}, using default")
      return
    
    # Now handle required variables (those without defaults)
    if vars_without_defaults:
      # Remove enabler from the list if it's there
      vars_without_defaults = [v for v in vars_without_defaults if v != enabler_var_name]
      
      for var_name in vars_without_defaults:
        var_data = variables[var_name]
        value = self._prompt_for_variable(var_name, var_data, required=True)
        self.final_values[var_name] = value
    
    # Handle variables with defaults
    if vars_with_defaults:
      # Remove enabler from the list
      remaining_vars = [v for v in vars_with_defaults if v != enabler_var_name]
      
      if remaining_vars:
        # Show preview and ask if they want to change values
        self._show_group_preview(group_name, remaining_vars)
        
        try:
          want_to_customize = Confirm.ask(f"Do you want to change {group_name} values?", default=False)
        except (EOFError, KeyboardInterrupt):
          logger.debug(f"User interrupted customization prompt for group {group_name}, using defaults")
          return
        
        if want_to_customize:
          for var_name in remaining_vars:
            var_data = variables[var_name]
            current_value = self.final_values[var_name]
            new_value = self._prompt_for_variable(var_name, var_data, required=False, current_value=current_value)
            self.final_values[var_name] = new_value
  
  def _show_summary(self):
    """Display a compact summary of all configured variables."""
    if not self.final_values:
      return
    
    # Only show detailed table if there are many variables (>5)
    if len(self.final_values) > 5:
      table = Table(box=box.SIMPLE)
      table.add_column("Variable", style="cyan")
      table.add_column("Value", style="green")
      
      for var_name, value in self.final_values.items():
        # Format value for display and truncate if too long
        if isinstance(value, list):
          display_value = ", ".join(str(item) for item in value)
        else:
          display_value = str(value)
        
        if len(display_value) > 50:
          display_value = display_value[:47] + "..."
        
        table.add_row(var_name, display_value)
      
      self.console.print(table)
    else:
      # For few variables, show a compact inline summary
      var_summaries = []
      for var_name, value in self.final_values.items():
        display_value = str(value)
        if len(display_value) > 20:
          display_value = display_value[:17] + "..."
        var_summaries.append(f"[cyan]{var_name}[/cyan]=[green]{display_value}[/green]")
      
      summary_text = ", ".join(var_summaries)
      self.console.print(f"\n[dim]Using:[/dim] {summary_text}")
    
    self.console.print()
    
    # Ask user if they want to proceed with template generation
    if not Confirm.ask("Proceed with generation?", default=True):
      raise KeyboardInterrupt("Template generation cancelled by user")
