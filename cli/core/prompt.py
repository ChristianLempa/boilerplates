"""Simplified prompt handler for template variables."""
from typing import Dict, Any, List, Tuple, Optional
from collections import OrderedDict
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
import logging
from .variables import TemplateVariable

logger = logging.getLogger('boilerplates')
console = Console()


class SimplifiedPromptHandler:
  """Prompt handler for template-detected variables."""
  
  def __init__(self, variables: Dict[str, TemplateVariable]):
    """Initialize with template variables.
    
    Args:
      variables: Dict of variable name to TemplateVariable object
    """
    self.variables = variables
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
    """Group variables by their prefix or enabler status.
    
    Returns:
      (groups, standalone) where groups is {prefix: [var_names]}
    """
    groups = OrderedDict()
    standalone = []
    
    # First pass: identify all groups
    for var_name, var in self.variables.items():
      if var.group:
        # This variable belongs to a group
        if var.group not in groups:
          groups[var.group] = []
        groups[var.group].append(var_name)
      else:
        # Check if this is an enabler for other variables
        # An enabler is a variable that other variables use as their group
        is_group_enabler = any(v.group == var_name for v in self.variables.values())
        if is_group_enabler:
          if var_name not in groups:
            groups[var_name] = []
          # The enabler itself is not added to the group list
        else:
          # Truly standalone variable
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
    
    # Check if this group has an enabler
    group_name = display_name.lower()
    enabler = None
    if is_group and group_name in self.variables:
      enabler_var = self.variables[group_name]
      if enabler_var.is_enabler:
        enabler = group_name
        # Ask about enabler first
        console.print(f"\n[bold cyan]{display_name} Configuration[/bold cyan]")
        enabled = Confirm.ask(
          f"Enable {enabler}?", 
          default=bool(enabler_var.default)
        )
        self.values[enabler] = enabled
        
        if not enabled:
          # Skip all group variables
          return
    
    # Split into required and optional
    required = []
    optional = []
    for var_name in var_names:
      var = self.variables[var_name]
      if var.is_required:
        required.append(var_name)
      else:
        optional.append(var_name)
    
    # Apply defaults
    for var_name in optional:
      self.values[var_name] = self.variables[var_name].default
    
    # Process required variables
    if required:
      if not enabler:  # Don't repeat header if we already showed it for enabler
        console.print(f"\n[bold cyan]{display_name} - Required Configuration[/bold cyan]")
      for var_name in required:
        var = self.variables[var_name]
        self.values[var_name] = self._prompt_variable(var, required=True)
    
    # Process optional variables
    if optional:
      # Filter out enabler variables from display
      display_optional = [v for v in optional if v != enabler]
      if display_optional:
        console.print(f"\n[bold cyan]{display_name} - Optional Configuration[/bold cyan]")
        self._show_variables_inline(display_optional)
      
      if display_optional and Confirm.ask("Do you want to change any values?", default=False):
        for var_name in optional:
          var = self.variables[var_name]
          self.values[var_name] = self._prompt_variable(
            var, current_value=self.values[var_name]
          )
  
  def _show_variables_inline(self, var_names: List[str]):
    """Display current variable values in a single line."""
    items = []
    for var_name in var_names:
      var = self.variables[var_name]
      value = self.values.get(var_name, var.default)
      if value is not None:
        # Format value based on type
        if isinstance(value, bool):
          formatted_value = str(value).lower()
        elif isinstance(value, str) and ' ' in value:
          formatted_value = f"'{value}'"
        else:
          formatted_value = str(value)
        items.append(f"{var.display_name}: {formatted_value}")
    
    if items:
      console.print(f"  [dim white]{', '.join(items)}[/dim white]")
  
  def _prompt_variable(
    self, 
    var: TemplateVariable, 
    required: bool = False,
    current_value: Any = None
  ) -> Any:
    """Prompt for a single variable value."""
    # Build prompt message
    parts = [f"Enter {var.display_name}"]
    if current_value is not None:
      parts.append(f"[dim]({current_value})[/dim]")
    elif required:
      parts.append("[red](Required)[/red]")
    
    prompt_msg = " ".join(parts)
    
    # Handle different types
    if var.type == 'boolean':
      default = bool(current_value) if current_value is not None else None
      return Confirm.ask(prompt_msg, default=default)
    
    elif var.type == 'integer':
      default = int(current_value) if current_value is not None else None
      while True:
        try:
          return IntPrompt.ask(prompt_msg, default=default)
        except ValueError:
          console.print("[red]Please enter a valid integer[/red]")
    
    elif var.type == 'float':
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
