from typing import Dict, Any, List, Optional
import logging
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.table import Table
from rich import box

logger = logging.getLogger('boilerplates')

class PromptHandler:
  """Prompt handler with Rich UI for variable configuration."""

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
    
    # Map prompt types to their handlers
    self.prompt_handlers = {
      'boolean': self._prompt_boolean,
      'integer': self._prompt_integer,
      'float': self._prompt_float,
      'choice': self._prompt_choice,
      'list': self._prompt_list,
      'string': self._prompt_string
    }
    
  def __call__(self) -> Dict[str, Any]:
    """Execute the prompting logic and return final variable values."""
    logger.debug(f"Starting prompt handler with {len(self.variable_groups)} variable groups")

    # Process groups in order (general first if exists)
    for group_name, group_data in self._get_ordered_groups():
      self._process_variable_group(group_name, group_data)
    
    self._show_summary()
    return self.final_values
  
  def _get_ordered_groups(self) -> List[tuple]:
    """Get groups in processing order (general first)."""
    ordered = []
    if 'general' in self.variable_groups:
      ordered.append(('general', self.variable_groups['general']))
    
    for name, data in self.variable_groups.items():
      if name != 'general':
        ordered.append((name, data))
    
    return ordered
  
  def _process_variable_group(self, group_name: str, group_data: Dict[str, Any]):
    """Process a single variable group."""
    variables = group_data.get('vars', {})
    if not variables:
      return

    # Flatten multivalue variables to check which ones are truly required
    required_items, optional_items = self._categorize_variables(variables)
    
    if not (required_items or optional_items):
      return
    
    # Apply defaults for all optional items
    for var_name, key, default_value in optional_items:
      if key is not None:
        # Multivalue with key
        if var_name not in self.final_values:
          self.final_values[var_name] = {}
        self.final_values[var_name][key] = default_value
      else:
        # Simple variable
        self.final_values[var_name] = default_value
    
    # Check for enabler variable
    enabler_var_name = group_data.get('enabler', '')
    has_enabler = enabler_var_name and enabler_var_name in variables
    
    # Determine if group should be processed
    if has_enabler:
      # Handle enabler group
      enabled = self._prompt_enabler(group_name, enabler_var_name)
      self.final_values[enabler_var_name] = enabled
      if not enabled:
        return
    elif not required_items:
      # No required items, ask if user wants to configure optional ones
      if not self._should_process_optional_group(group_name):
        return
    
    # Show group header
    self._show_group_header(group_name, group_data)
    
    # Process required items first
    if required_items:
      for var_name, key, _ in required_items:
        if var_name == enabler_var_name:
          continue  # Already handled
        
        if key is not None:
          # Multivalue required key
          value = self._prompt_for_multivalue_key(
            var_name, key, variables[var_name], required=True
          )
          if var_name not in self.final_values:
            self.final_values[var_name] = {}
          self.final_values[var_name][key] = value
        else:
          # Simple required variable
          self.final_values[var_name] = self._prompt_for_variable(
            var_name, variables[var_name], required=True
          )
    
    # Process optional items if user wants to change them
    # Filter out already-prompted items from required_items
    already_prompted = set((var_name, key) for var_name, key, _ in required_items)
    optional_to_prompt = [
      (var_name, key, default) for var_name, key, default in optional_items 
      if var_name != enabler_var_name and (var_name, key) not in already_prompted
    ]
    
    if optional_to_prompt:
      self._handle_optional_items(group_name, optional_to_prompt, variables)
  
  def _handle_optional_items(self, group_name: str, optional_items: list, variables: Dict[str, Any]):
    """Handle optional items (variables or multivalue keys with defaults)."""
    # Group items by variable for preview
    vars_to_show = {}
    for var_name, key, default in optional_items:
      if var_name not in vars_to_show:
        vars_to_show[var_name] = []
      vars_to_show[var_name].append((key, default))
    
    # Show preview
    self._show_preview(list(vars_to_show.keys()))
    
    # Ask if user wants to customize
    try:
      want_to_customize = Confirm.ask(f"Do you want to change {group_name} values?", default=False)
    except (EOFError, KeyboardInterrupt):
      logger.debug(f"User interrupted customization for {group_name}, using defaults")
      return
    
    if want_to_customize:
      for var_name, key, default in optional_items:
        var_data = variables[var_name]
        
        if key is not None:
          # Multivalue item
          value = self._prompt_for_multivalue_key(
            var_name, key, var_data, required=False
          )
          if isinstance(key, int):
            # Handle list index
            if var_name not in self.final_values:
              self.final_values[var_name] = []
            while len(self.final_values[var_name]) <= key:
              self.final_values[var_name].append(None)
            self.final_values[var_name][key] = value
          else:
            # Handle dict key
            if var_name not in self.final_values:
              self.final_values[var_name] = {}
            self.final_values[var_name][key] = value
        else:
          # Simple variable
          current_value = self.final_values.get(var_name)
          self.final_values[var_name] = self._prompt_for_variable(
            var_name, var_data, required=False, current_value=current_value
          )
  
  def _categorize_variables(self, variables: Dict[str, Any]) -> tuple:
    """Categorize variables into required and optional items.
    
    Returns:
      (required_items, optional_items) where each item is (var_name, key_or_index, default_value)
      For simple variables, key_or_index is None.
    """
    required_items = []
    optional_items = []
    
    for var_name, var_data in variables.items():
      patterns = var_data.get('usage_patterns', {})
      
      if patterns and patterns.get('keys'):
        # Multivalue with specific keys
        for key in patterns['keys']:
          # Check if this specific key has a default
          default = None
          if var_name in self.resolved_defaults and isinstance(self.resolved_defaults[var_name], dict):
            default = self.resolved_defaults[var_name].get(key)
          
          if default is None:
            required_items.append((var_name, key, None))
          else:
            optional_items.append((var_name, key, default))
      
      elif patterns and patterns.get('indices'):
        # Multivalue with specific indices  
        for idx in patterns['indices']:
          # Check if this specific index has a default
          default = None
          if var_name in self.resolved_defaults and isinstance(self.resolved_defaults[var_name], list):
            if idx < len(self.resolved_defaults[var_name]):
              default = self.resolved_defaults[var_name][idx]
          
          if default is None:
            required_items.append((var_name, idx, None))
          else:
            optional_items.append((var_name, idx, default))
      
      else:
        # Simple variable
        default = self.resolved_defaults.get(var_name)
        if default is None:
          required_items.append((var_name, None, None))
        else:
          optional_items.append((var_name, None, default))
    
    return required_items, optional_items
  
  def _prompt_for_multivalue_key(self, var_name: str, key, var_data: Dict[str, Any], required: bool = False) -> Any:
    """Prompt for a specific key/index of a multivalue variable."""
    var_type = var_data.get('type', 'string')
    
    # Build prompt message
    if isinstance(key, int):
      prompt_msg = f"{var_name}[{key}]"
    else:
      prompt_msg = f"{var_name}['{key}']"
    
    if var_data.get('description'):
      prompt_msg = f"Enter {prompt_msg} ({var_data['description']})"
    else:
      prompt_msg = f"Enter {prompt_msg}"
    
    if required:
      prompt_msg += " [red](Required)[/red]"
    
    # Get current value if exists
    current_value = None
    if var_name in self.final_values:
      if isinstance(self.final_values[var_name], dict) and key in self.final_values[var_name]:
        current_value = self.final_values[var_name][key]
      elif isinstance(self.final_values[var_name], list) and isinstance(key, int) and key < len(self.final_values[var_name]):
        current_value = self.final_values[var_name][key]
    
    # Prompt based on type
    handler = self.prompt_handlers.get(var_type, self.prompt_handlers['string'])
    if var_type == 'string':
      return handler(prompt_msg, current_value, required)
    else:
      return handler(prompt_msg, current_value)
  
  def _should_process_optional_group(self, group_name: str) -> bool:
    """Ask if user wants to configure optional settings for a group."""
    try:
      return Confirm.ask(f"Do you want to configure {group_name} settings?", default=False)
    except (EOFError, KeyboardInterrupt):
      return False
  
  
  def _prompt_enabler(self, group_name: str, enabler_var_name: str) -> bool:
    """Prompt for a group enabler variable."""
    current_value = self.final_values.get(enabler_var_name, False)
    try:
      return Confirm.ask(
        f"Do you want to enable [bold]{group_name}[/bold]?",
        default=bool(current_value)
      )
    except (EOFError, KeyboardInterrupt):
      logger.debug(f"User interrupted enabler prompt for {group_name}")
      return False
  
  def _show_group_header(self, group_name: str, group_data: Dict[str, Any]):
    """Display group header."""
    icon = group_data.get('icon', '')
    display_name = group_data.get('display_name', group_name.title())
    icon_display = f"{icon} " if icon else ""
    self.console.print(f"\n{icon_display}[bold magenta]{display_name} Variables[/bold magenta]")
  
  
  def _show_preview(self, variables: List[str]):
    """Show preview of configured values."""
    if not variables:
      return
    
    previews = []
    for var_name in variables:
      value = self.final_values.get(var_name)
      if value is None:
        display_value = "not set"
      elif isinstance(value, dict):
        # Show dict values compactly
        items = [f"{k}={v}" for k, v in value.items()]
        display_value = "{" + ", ".join(items[:2]) + ("..." if len(items) > 2 else "") + "}"
      elif isinstance(value, list):
        # Show list values compactly
        display_value = "[" + ", ".join(str(v) for v in value[:2]) + (", ..." if len(value) > 2 else "") + "]"
      else:
        display_value = str(value)[:22] + "..." if len(str(value)) > 25 else str(value)
      previews.append(f"{var_name}={display_value}")
    
    self.console.print(f"[dim white]({', '.join(previews)})[/dim white]")
  
  
  def _prompt_for_variable(self, var_name: str, var_data: Dict[str, Any], required: bool = False, current_value: Any = None) -> Any:
    """Prompt user for a single variable.
    
    Note: Multivalue variables with patterns are handled separately via _prompt_for_multivalue_key.
    This method only handles simple variables or multivalue without specific patterns.
    """
    var_type = var_data.get('type', 'string')
    
    # Build prompt message
    prompt_message = self._build_prompt_message(var_name, var_data, required, current_value)
    
    # Get handler and execute prompt
    handler = self.prompt_handlers.get(var_type, self.prompt_handlers['string'])
    
    try:
      # Special handling for choice type (needs options)
      if var_type == 'choice':
        return handler(prompt_message, current_value, var_data.get('options', []))
      # Special handling for string type (needs required flag)
      elif var_type == 'string':
        return handler(prompt_message, current_value, required)
      else:
        return handler(prompt_message, current_value)
    except KeyboardInterrupt:
      raise
    except Exception as e:
      logger.error(f"Error prompting for {var_name}: {e}")
      self.console.print(f"[red]Error getting input for {var_name}[/red]")
      # Fallback to string prompt
      return self._prompt_string(prompt_message, current_value, required)
  
  def _build_prompt_message(self, var_name: str, var_data: Dict[str, Any], required: bool, current_value: Any) -> str:
    """Build the prompt message for a variable."""
    parts = ["Enter", f"[bold]{var_name}[/bold]"]
    
    if description := var_data.get('description'):
      parts.append(f"({description})")
    
    if current_value is not None:
      parts.append(f"[dim]({current_value})[/dim]")
    elif required:
      parts.append("[red](Required)[/red]")
    
    return " ".join(parts)
  
  def _prompt_string(self, prompt_message: str, current_value: Any = None, required: bool = False) -> str:
    """Prompt for string input."""
    default = str(current_value) if current_value is not None else None
    
    while True:
      try:
        value = Prompt.ask(prompt_message, default=default) or ""
        
        if required and not value.strip():
          self.console.print("[red]This field is required[/red]")
          continue
          
        return value.strip()
      except (EOFError, KeyboardInterrupt):
        raise KeyboardInterrupt("Operation cancelled by user")
  
  def _prompt_boolean(self, prompt_message: str, current_value: Any = None) -> bool:
    """Prompt for boolean input."""
    default = bool(current_value) if current_value is not None else None
    try:
      return Confirm.ask(prompt_message, default=default)
    except (EOFError, KeyboardInterrupt):
      raise KeyboardInterrupt("Operation cancelled by user")
  
  def _prompt_integer(self, prompt_message: str, current_value: Any = None) -> int:
    """Prompt for integer input."""
    default = int(current_value) if current_value is not None else None
    
    while True:
      try:
        return IntPrompt.ask(prompt_message, default=default)
      except ValueError:
        self.console.print("[red]Please enter a valid integer[/red]")
      except (EOFError, KeyboardInterrupt):
        raise KeyboardInterrupt("Operation cancelled by user")
  
  def _prompt_float(self, prompt_message: str, current_value: Any = None) -> float:
    """Prompt for float input."""
    default = float(current_value) if current_value is not None else None
    
    while True:
      try:
        return FloatPrompt.ask(prompt_message, default=default)
      except ValueError:
        self.console.print("[red]Please enter a valid number[/red]")
      except (EOFError, KeyboardInterrupt):
        raise KeyboardInterrupt("Operation cancelled by user")
  
  def _prompt_choice(self, prompt_message: str, current_value: Any = None, options: List[Any] = None) -> Any:
    """Prompt for choice from options."""
    if not options:
      return self._prompt_string(prompt_message, current_value)
    
    # Show options
    self.console.print("\n[dim]Available options:[/dim]")
    for i, option in enumerate(options, 1):
      marker = "→" if option == current_value else " "
      self.console.print(f"  {marker} {i}. {option}")
    
    while True:
      try:
        choice = Prompt.ask(f"{prompt_message} (1-{len(options)})")
        
        # Try numeric selection
        try:
          idx = int(choice) - 1
          if 0 <= idx < len(options):
            return options[idx]
        except ValueError:
          # Try string match
          matches = [opt for opt in options if str(opt).lower() == choice.lower()]
          if matches:
            return matches[0]
        
        self.console.print(f"[red]Invalid choice. Enter 1-{len(options)} or option name[/red]")
      except (EOFError, KeyboardInterrupt):
        raise KeyboardInterrupt("Operation cancelled by user")
  
  def _prompt_list(self, prompt_message: str, current_value: Any = None) -> List[str]:
    """Prompt for list input (comma-separated)."""
    default = ", ".join(str(item) for item in current_value) if isinstance(current_value, list) else str(current_value or "")
    
    self.console.print("[dim]Enter values separated by commas[/dim]")
    
    try:
      value = Prompt.ask(prompt_message, default=default)
      return [item.strip() for item in value.split(',') if item.strip()] if value.strip() else []
    except (EOFError, KeyboardInterrupt):
      raise KeyboardInterrupt("Operation cancelled by user")
  
  def _show_summary(self):
    """Display summary of configured variables."""
    if not self.final_values:
      return
    
    # Compact summary for few variables, table for many
    if len(self.final_values) <= 5:
      summaries = []
      for name, value in self.final_values.items():
        display_value = self._truncate_value(value, 20)
        summaries.append(f"[cyan]{name}[/cyan]=[green]{display_value}[/green]")
      self.console.print(f"\n[dim]Using:[/dim] {', '.join(summaries)}")
    else:
      table = Table(box=box.SIMPLE)
      table.add_column("Variable", style="cyan")
      table.add_column("Value", style="green")
      
      for name, value in self.final_values.items():
        display_value = self._truncate_value(value, 50)
        table.add_row(name, display_value)
      
      self.console.print(table)
    
    self.console.print()
    
    # Confirm generation
    if not Confirm.ask("Proceed with generation?", default=True):
      raise KeyboardInterrupt("Generation cancelled by user")
  
  def _truncate_value(self, value: Any, max_length: int) -> str:
    """Truncate value for display."""
    display_value = ", ".join(str(item) for item in value) if isinstance(value, list) else str(value)
    return display_value[:max_length-3] + "..." if len(display_value) > max_length else display_value
