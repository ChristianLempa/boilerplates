from collections import OrderedDict
from typing import Dict, Optional, Any, List

from rich.table import Table

from .variables import VariableCollection


def render_variable_table(
  variables: VariableCollection,
  title: str = "Variables",
  show_options: bool = False,
  sections: Optional[OrderedDict[str, Dict[str, Any]]] = None,
) -> Table:
  """Build a Rich table representing variable metadata."""

  table = Table(title=title, header_style="bold cyan")
  table.add_column("Name", style="cyan", no_wrap=True)
  table.add_column("Type", style="yellow", no_wrap=True)
  if show_options:
    table.add_column("Options", style="magenta")
  table.add_column("Default", style="green", no_wrap=True)
  table.add_column("Description", style="white")

  rows_by_name: Dict[str, Dict[str, str]] = {
    row["name"]: row for row in variables.as_rows()
  }

  def _style_value(value: str, enabled: bool) -> str:
    if enabled or not value:
      return value
    return f"[grey50]{value}[/grey50]"

  def _add_variable_row(row: Dict[str, str], *, enabled: bool = True) -> None:
    cells = [
      _style_value(row["name"], enabled),
      _style_value(row["type"], enabled),
    ]
    if show_options:
      options = ", ".join(row["options"]) if row["options"] else ""
      cells.append(_style_value(options, enabled))
    cells.extend(
      [
        _style_value(row["default"], enabled),
        _style_value(row["description"], enabled),
      ]
    )
    style = None if enabled else "grey50"
    table.add_row(*cells, style=style)

  if sections:
    column_count = 4 + (1 if show_options else 0)
    for idx, meta in enumerate(sections.values()):
      title = meta.get("title") or "Section"
      names = meta.get("variables", [])
      toggle_var = None
      toggle_name = meta.get("toggle")
      if toggle_name:
        toggle_var = variables.get_variable(toggle_name)
      enabled = True
      if toggle_var is not None:
        try:
          enabled = bool(toggle_var.get_typed_value())
        except ValueError:
          enabled = True

      header_style = "bold magenta" if enabled else "bold grey50"
      header_title = title if enabled else f"{title} (disabled)"
      header_cells = [
        _style_value(header_title, enabled)
      ] + ["" for _ in range(column_count - 1)]
      table.add_row(*header_cells, style=header_style, end_section=False)
      for name in names:
        row = rows_by_name.get(name)
        if not row:
          continue
        _add_variable_row(row, enabled=enabled)
      if idx != len(sections) - 1:
        table.add_section()
  else:
    for row in rows_by_name.values():
      _add_variable_row(row)

  return table


def render_template_list_table(
  templates: List[Any],
  module_name: str,
  *,
  include_library: bool = False,
) -> Table:
  """Build a Rich table for template listings without extra info lines.
  
  Columns and formatting:
    - ID (with dimmed (version) suffix if available)
    - Name
    - Description (takes remaining width, truncates with ellipsis)
    - Author (last column)
  """
  table = Table(title=f"{module_name.title()} Templates", header_style="bold cyan", expand=True)

  # Constrain non-description columns to preserve space
  table.add_column("ID", style="cyan", no_wrap=True, max_width=28, overflow="ellipsis")
  table.add_column("Name", style="white", no_wrap=True, max_width=28, overflow="ellipsis")
  if include_library:
    table.add_column("Library", style="magenta", no_wrap=True, max_width=16, overflow="ellipsis")
  # Description gets most space via ratio and truncates with ellipsis
  table.add_column("Description", style="white", no_wrap=True, overflow="ellipsis", ratio=1)
  table.add_column("Author", style="yellow", no_wrap=True, max_width=24, overflow="ellipsis")

  for tpl in templates:
    _id = tpl.id or "-"
    _ver = tpl.version or ""
    id_with_ver = f"{_id} [dim]({_ver})[/dim]" if _ver else _id
    name = tpl.name or _id
    author = tpl.author or "-"
    desc = tpl.description or "-"
    if include_library:
      library = tpl.library or "-"
      table.add_row(id_with_ver, name, library, desc, author)
    else:
      table.add_row(id_with_ver, name, desc, author)

  return table
