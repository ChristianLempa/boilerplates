"""Simplified prompt handler for dotted notation variables."""
from typing import Dict, Any, List, Tuple, Optional
from collections import OrderedDict
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
import logging

logger = logging.getLogger('boilerplates')
console = Console()


class SimplifiedPromptHandler:
  """Clean prompt handler for dotted notation variables."""
  
  def __init__(self, variables: Dict[str, Any], defaults: Dict[str, Any], dict_keys: Dict[str, List[str]] = None):
    """Initialize with template variables and defaults.
    
    Args:
      variables: Dict of variable name to Variable object
      defaults: Dict of variable name to default value
      dict_keys: Dict variables and their keys used in template
    """
    self.variables = variables
    self.defaults = defaults
    self.dict_keys = dict_keys or {}
    self.values = {}
    
  def __call__(self) -> Dict[str, Any]:
    """Execute the prompting flow."""
    # Group variables by prefix (preserves registration order)
    groups, standalone = self._group_variables()
    
    # Process standalone variables first as "General" group
    if standalone:
      self._process_variable_set("General", standalone, is_group=False)
    
    # Process each group in the order they were registered
    for group_name, group_vars in groups.items():
      self._process_variable_set(group_name.title(), group_vars, is_group=True)
    
    return self.values
  
  def _group_variables(self) -> Tuple[Dict[str, List[str]], List[str]]:
    """Group variables by their prefix, preserving registration order.
    
    Returns:
      (groups, standalone) where groups is {prefix: [var_names]}
    """
    groups = OrderedDict()
    standalone = []
    
    # Process variables in registration order
    for var_name in self.variables.keys():
      if '.' in var_name:
        # This is a child variable (e.g., 'traefik.host')
        prefix = var_name.split('.')[0]
        
        # Create group if needed (preserves first encounter order)
        if prefix not in groups:
          groups[prefix] = []
        
        # Add to group
        groups[prefix].append(var_name)
      else:
        # Standalone variable (no dots)
        standalone.append(var_name)
    
    return groups, standalone
  
  def _process_variable_set(self, display_name: str, var_names: List[str], 
                            is_group: bool = False):
    """Unified method to process any set of variables.
    
    Args:
        display_name: Name to show in the header
        var_names: List of variable names to process
        is_group: Whether this is a group (vs standalone)
    """
    # Deduplicate variables
    var_names = list(dict.fromkeys(var_names))  # Preserves order while removing duplicates
    
    # Check if this group has an enabler (standalone variable with same name as group)
    group_name = display_name.lower()
    enabler = None
    if is_group and group_name in self.variables:
      enabler = group_name
      # Ask about enabler first
      console.print(f"\n[bold cyan]{display_name} Configuration[/bold cyan]")
      var = self.variables[enabler]
      enabled = Confirm.ask(
        f"Enable {enabler}?", 
        default=bool(self.defaults.get(enabler, False))
      )
      self.values[enabler] = enabled
      
      if not enabled:
        # Skip all group variables
        return
    
    # Split into required and optional
    required = []
    optional = []
    for var_name in var_names:
      if var_name in self.defaults:
        optional.append(var_name)
      else:
        required.append(var_name)
    
    # Apply defaults
    for var_name in optional:
      self.values[var_name] = self.defaults[var_name]
    
    # Process required variables
    if required:
      if not enabler:  # Don't repeat header if we already showed it for enabler
        console.print(f"\n[bold cyan]{display_name} - Required Configuration[/bold cyan]")
      for var_name in required:
        var = self.variables[var_name]
        if var_name in self.dict_keys:
          console.print(f"\n[cyan]{var.description or var_name}[/cyan]")
          self.values[var_name] = self._prompt_dict_variable(var_name, var)
        else:
          display = var_name.replace('.', ' ') if is_group else var_name
          self.values[var_name] = self._prompt_variable(display, var, required=True)
    
    # Process optional variables
    if optional:
      console.print(f"\n[bold cyan]{display_name} - Optional Configuration[/bold cyan]")
      # Filter out enabler variables from display
      display_optional = [v for v in optional if v != enabler]
      if display_optional:
        self._show_variables(display_optional)
      
      if Confirm.ask("Do you want to change any values?", default=False):
        for var_name in optional:
          # Skip the enabler variable as it was already handled
          if var_name == enabler:
            continue
          var = self.variables[var_name]
          if var_name in self.dict_keys:
            console.print(f"\n[cyan]{var.description or var_name}[/cyan]")
            self.values[var_name] = self._prompt_dict_variable(
              var_name, var, current_values=self.values.get(var_name, {})
            )
          else:
            display = var_name.replace('.', ' ') if is_group else var_name
            self.values[var_name] = self._prompt_variable(
              display, var, current_value=self.values[var_name]
            )
  
  
  def _prompt_dict_variable(self, var_name: str, var: Any, current_values: Dict[str, Any] = None) -> Dict[str, Any]:
    """Prompt for a dict variable with dynamic keys."""
    result = {}
    keys = self.dict_keys.get(var_name, [])
    current_values = current_values or {}
    
    for key in keys:
      # Use current value if available, otherwise check for default
      current_value = current_values.get(key)
      if current_value is None:
        if var_name in self.defaults and isinstance(self.defaults[var_name], dict):
          current_value = self.defaults[var_name].get(key)
      
      prompt_msg = f"Enter {var_name}['{key}']"
      if current_value is not None:
        prompt_msg += f" [dim]({current_value})[/dim]"
      else:
        prompt_msg += " [red](Required)[/red]"
      
      # Infer type from current value or default
      if isinstance(current_value, int):
        while True:
          try:
            result[key] = IntPrompt.ask(prompt_msg, default=current_value)
            break
          except ValueError:
            console.print("[red]Please enter a valid integer[/red]")
      elif isinstance(current_value, bool):
        result[key] = Confirm.ask(prompt_msg, default=current_value)
      else:
        value = Prompt.ask(prompt_msg, default=str(current_value) if current_value else None)
        result[key] = value if value else current_value
    
    return result
  
  def _show_variables(self, var_names: List[str]):
    """Display current variable values."""
    for var_name in var_names:
      value = self.values.get(var_name, self.defaults.get(var_name))
      if value is not None:
        display_name = var_name.replace('.', ' ')
        # Special formatting for dict values - show each key separately
        if isinstance(value, dict):
          for key, val in value.items():
            console.print(f"  {display_name}['{key}']: [dim]{val}[/dim]")
        else:
          console.print(f"  {display_name}: [dim]{value}[/dim]")
  
  def _prompt_variable(
    self, 
    name: str, 
    var: Any, 
    required: bool = False,
    current_value: Any = None
  ) -> Any:
    """Prompt for a single variable value."""
    var_type = var.type if hasattr(var, 'type') else 'string'
    description = var.description if hasattr(var, 'description') else ''
    
    # Build prompt message
    parts = [f"Enter {name}"]
    if description:
      parts.append(f"({description})")
    if current_value is not None:
      parts.append(f"[dim]({current_value})[/dim]")
    elif required:
      parts.append("[red](Required)[/red]")
    
    prompt_msg = " ".join(parts)
    
    # Handle different types
    if var_type == 'boolean':
      default = bool(current_value) if current_value is not None else None
      return Confirm.ask(prompt_msg, default=default)
    
    elif var_type == 'integer':
      default = int(current_value) if current_value is not None else None
      while True:
        try:
          return IntPrompt.ask(prompt_msg, default=default)
        except ValueError:
          console.print("[red]Please enter a valid integer[/red]")
    
    elif var_type == 'float':
      default = float(current_value) if current_value is not None else None
      while True:
        try:
          return FloatPrompt.ask(prompt_msg, default=default)
        except ValueError:
          console.print("[red]Please enter a valid number[/red]")
    
    else:  # string
      default = str(current_value) if current_value is not None else None
      while True:
        value = Prompt.ask(prompt_msg, default=default) or ""
        if required and not value.strip():
          console.print("[red]This field is required[/red]")
          continue
        return value.strip()
