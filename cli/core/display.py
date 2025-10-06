from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

if TYPE_CHECKING:
    from .template import Template

logger = logging.getLogger(__name__)
console = Console()


class IconManager:
    """Centralized icon management system for consistent CLI display.
    
    This class provides standardized icons for file types, status indicators,
    and UI elements. Icons use Nerd Font glyphs for consistent display.
    
    Categories:
        - File types: .yaml, .j2, .json, .md, etc.
        - Status: success, warning, error, info, skipped
        - UI elements: folders, config, locks, etc.
    """

    # File Type Icons
    FILE_FOLDER = "\uf07b"          # 
    FILE_DEFAULT = "\uf15b"         # 
    FILE_YAML = "\uf15c"            # 
    FILE_JSON = "\ue60b"            # 
    FILE_MARKDOWN = "\uf48a"        # 
    FILE_JINJA2 = "\ue235"          # 
    FILE_DOCKER = "\uf308"          # 
    FILE_COMPOSE = "\uf308"         # 
    FILE_SHELL = "\uf489"           # 
    FILE_PYTHON = "\ue73c"          # 
    FILE_TEXT = "\uf15c"            # 
    
    # Status Indicators
    STATUS_SUCCESS = "\uf00c"       #  (check)
    STATUS_ERROR = "\uf00d"         #  (times/x)
    STATUS_WARNING = "\uf071"       #  (exclamation-triangle)
    STATUS_INFO = "\uf05a"          #  (info-circle)
    STATUS_SKIPPED = "\uf05e"       #  (ban/circle-slash)
    
    # UI Elements
    UI_CONFIG = "\ue5fc"            # 
    UI_LOCK = "\uf084"              # 
    UI_SETTINGS = "\uf013"          # 
    UI_ARROW_RIGHT = "\uf061"       #  (arrow-right)
    UI_BULLET = "\uf111"            #  (circle)
    
    @classmethod
    def get_file_icon(cls, file_path: str | Path) -> str:
        """Get the appropriate icon for a file based on its extension or name.
        
        Args:
            file_path: Path to the file (can be string or Path object)
            
        Returns:
            Unicode icon character for the file type
            
        Examples:
            >>> IconManager.get_file_icon("config.yaml")
            '\uf15c'
            >>> IconManager.get_file_icon("template.j2")
            '\ue235'
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        file_name = file_path.name.lower()
        suffix = file_path.suffix.lower()
        
        # Check for Docker Compose files
        compose_names = {
            "docker-compose.yml", "docker-compose.yaml",
            "compose.yml", "compose.yaml"
        }
        if file_name in compose_names or file_name.startswith("docker-compose"):
            return cls.FILE_DOCKER
        
        # Check by extension
        extension_map = {
            ".yaml": cls.FILE_YAML,
            ".yml": cls.FILE_YAML,
            ".json": cls.FILE_JSON,
            ".md": cls.FILE_MARKDOWN,
            ".j2": cls.FILE_JINJA2,
            ".sh": cls.FILE_SHELL,
            ".py": cls.FILE_PYTHON,
            ".txt": cls.FILE_TEXT,
        }
        
        return extension_map.get(suffix, cls.FILE_DEFAULT)
    
    @classmethod
    def get_status_icon(cls, status: str) -> str:
        """Get the appropriate icon for a status indicator.
        
        Args:
            status: Status type (success, error, warning, info, skipped)
            
        Returns:
            Unicode icon character for the status
            
        Examples:
            >>> IconManager.get_status_icon("success")
            '✓'
            >>> IconManager.get_status_icon("warning")
            '⚠'
        """
        status_map = {
            "success": cls.STATUS_SUCCESS,
            "error": cls.STATUS_ERROR,
            "warning": cls.STATUS_WARNING,
            "info": cls.STATUS_INFO,
            "skipped": cls.STATUS_SKIPPED,
        }
        return status_map.get(status.lower(), cls.STATUS_INFO)
    
    @classmethod
    def folder(cls) -> str:
        """Get the folder icon."""
        return cls.FILE_FOLDER
    
    @classmethod
    def config(cls) -> str:
        """Get the config icon."""
        return cls.UI_CONFIG
    
    @classmethod
    def lock(cls) -> str:
        """Get the lock icon (for sensitive variables)."""
        return cls.UI_LOCK
    
    @classmethod
    def arrow_right(cls) -> str:
        """Get the right arrow icon (for showing transitions/changes)."""
        return cls.UI_ARROW_RIGHT


class DisplayManager:
    """Handles all rich rendering for the CLI."""

    def display_templates_table(
        self, templates: list, module_name: str, title: str
    ) -> None:
        """Display a table of templates.
        
        Args:
            templates: List of Template objects
            module_name: Name of the module
            title: Title for the table
        """
        if not templates:
            logger.info(f"No templates found for module '{module_name}'")
            return

        logger.info(f"Listing {len(templates)} templates for module '{module_name}'")
        table = Table(title=title)
        table.add_column("ID", style="bold", no_wrap=True)
        table.add_column("Name")
        table.add_column("Tags")
        table.add_column("Version", no_wrap=True)
        table.add_column("Library", no_wrap=True)

        for template in templates:
            name = template.metadata.name or "Unnamed Template"
            tags_list = template.metadata.tags or []
            tags = ", ".join(tags_list) if tags_list else "-"
            version = str(template.metadata.version) if template.metadata.version else ""
            library = template.metadata.library or ""

            table.add_row(template.id, name, tags, version, library)

        console.print(table)

    def display_template_details(self, template: Template, template_id: str) -> None:
        """Display template information panel and variables table."""
        self._display_template_header(template, template_id)
        self._display_file_tree(template)
        self._display_variables_table(template)

    def display_section_header(self, title: str, description: str | None) -> None:
        """Display a section header."""
        if description:
            console.print(f"\n[bold cyan]{title}[/bold cyan] [dim]- {description}[/dim]")
        else:
            console.print(f"\n[bold cyan]{title}[/bold cyan]")
        console.print("─" * 40, style="dim")

    def display_validation_error(self, message: str) -> None:
        """Display a validation error message."""
        self.display_message('error', message)
    
    def display_message(self, level: str, message: str, context: str | None = None) -> None:
        """Display a message with consistent formatting.
        
        Args:
            level: Message level (error, warning, success, info)
            message: The message to display
            context: Optional context information
        """
        icon = IconManager.get_status_icon(level)
        colors = {'error': 'red', 'warning': 'yellow', 'success': 'green', 'info': 'blue'}
        color = colors.get(level, 'white')
        
        # Format message based on context
        if context:
            text = f"{level.capitalize()} in {context}: {message}" if level == 'error' or level == 'warning' else f"{context}: {message}"
        else:
            text = f"{level.capitalize()}: {message}" if level == 'error' or level == 'warning' else message
        
        console.print(f"[{color}]{icon} {text}[/{color}]")
        
        # Log appropriately
        log_message = f"{context}: {message}" if context else message
        log_methods = {'error': logger.error, 'warning': logger.warning, 'success': logger.info, 'info': logger.info}
        log_methods.get(level, logger.info)(log_message)
    
    def display_error(self, message: str, context: str | None = None) -> None:
        """Display an error message."""
        self.display_message('error', message, context)
    
    def display_warning(self, message: str, context: str | None = None) -> None:
        """Display a warning message."""
        self.display_message('warning', message, context)
    
    def display_success(self, message: str, context: str | None = None) -> None:
        """Display a success message."""
        self.display_message('success', message, context)
    
    def display_info(self, message: str, context: str | None = None) -> None:
        """Display an informational message."""
        self.display_message('info', message, context)

    def _display_template_header(self, template: Template, template_id: str) -> None:
        """Display the header for a template."""
        template_name = template.metadata.name or "Unnamed Template"
        version = str(template.metadata.version) if template.metadata.version else "Not specified"
        description = template.metadata.description or "No description available"

        console.print(
            f"[bold blue]{template_name} ({template_id} - [cyan]{version}[/cyan])[/bold blue]"
        )
        console.print(description)

    def _build_file_tree(self, root_label: str, files: list, get_file_info: callable) -> Tree:
        """Build a file tree structure.
        
        Args:
            root_label: Label for root node
            files: List of files to display
            get_file_info: Function that takes a file and returns (path, display_name, color, extra_text)
        
        Returns:
            Tree object ready for display
        """
        file_tree = Tree(root_label)
        tree_nodes = {Path("."): file_tree}
        
        for file_item in sorted(files, key=lambda f: get_file_info(f)[0]):
            path, display_name, color, extra_text = get_file_info(file_item)
            parts = path.parts
            current_path = Path(".")
            current_node = file_tree
            
            # Build directory structure
            for part in parts[:-1]:
                current_path = current_path / part
                if current_path not in tree_nodes:
                    new_node = current_node.add(f"{IconManager.folder()} [white]{part}[/white]")
                    tree_nodes[current_path] = new_node
                current_node = tree_nodes[current_path]
            
            # Add file
            icon = IconManager.get_file_icon(display_name)
            file_label = f"{icon} [{color}]{display_name}[/{color}]"
            if extra_text:
                file_label += f" {extra_text}"
            current_node.add(file_label)
        
        return file_tree
    
    def _display_file_tree(self, template: Template) -> None:
        """Display the file structure of a template."""
        console.print()
        console.print("[bold blue]Template File Structure:[/bold blue]")
        
        def get_template_file_info(template_file):
            display_name = template_file.output_path.name if hasattr(template_file, 'output_path') else template_file.relative_path.name
            return (template_file.relative_path, display_name, 'white', None)
        
        file_tree = self._build_file_tree(
            f"{IconManager.folder()} [white]{template.id}[/white]",
            template.template_files,
            get_template_file_info
        )
        
        if file_tree.children:
            console.print(file_tree)

    def _display_variables_table(self, template: Template) -> None:
        """Display a table of variables for a template."""
        if not (template.variables and template.variables.has_sections()):
            return

        console.print()
        console.print("[bold blue]Template Variables:[/bold blue]")

        variables_table = Table(show_header=True, header_style="bold blue")
        variables_table.add_column("Variable", style="white", no_wrap=True)
        variables_table.add_column("Type", style="magenta")
        variables_table.add_column("Default", style="green")
        variables_table.add_column("Description", style="white")

        first_section = True
        for section in template.variables.get_sections().values():
            if not section.variables:
                continue

            if not first_section:
                variables_table.add_row("", "", "", "", style="bright_black")
            first_section = False

            # Check if section is enabled AND dependencies are satisfied
            is_enabled = section.is_enabled()
            dependencies_satisfied = template.variables.is_section_satisfied(section.key)
            is_dimmed = not (is_enabled and dependencies_satisfied)

            # Only show (disabled) if section has no dependencies (dependencies make it obvious)
            disabled_text = " (disabled)" if (is_dimmed and not section.needs) else ""
            
            # For disabled sections, make entire heading bold and dim (don't include colored markup inside)
            if is_dimmed:
                # Build text without internal markup, then wrap entire thing in bold bright_black (dimmed appearance)
                required_part = " (required)" if section.required else ""
                needs_part = ""
                if section.needs:
                    needs_list = ", ".join(section.needs)
                    needs_part = f" (needs: {needs_list})"
                header_text = f"[bold bright_black]{section.title}{required_part}{needs_part}{disabled_text}[/bold bright_black]"
            else:
                # For enabled sections, include the colored markup
                required_text = " [yellow](required)[/yellow]" if section.required else ""
                needs_text = ""
                if section.needs:
                    needs_list = ", ".join(section.needs)
                    needs_text = f" [dim](needs: {needs_list})[/dim]"
                header_text = f"[bold]{section.title}{required_text}{needs_text}{disabled_text}[/bold]"
            variables_table.add_row(header_text, "", "", "")

            for var_name, variable in section.variables.items():
                row_style = "bright_black" if is_dimmed else None
                
                # Build default value display
                # If origin is 'config' and original value differs from current, show: original → config_value
                if (variable.origin == "config" and 
                    hasattr(variable, '_original_stored') and
                    variable.original_value != variable.value):
                    # Format original value (use same display logic, but shorter)
                    if variable.sensitive:
                        orig_display = "********"
                    elif variable.original_value is None or variable.original_value == "":
                        orig_display = "[dim](none)[/dim]"
                    else:
                        orig_val_str = str(variable.original_value)
                        orig_display = orig_val_str[:15] + "..." if len(orig_val_str) > 15 else orig_val_str
                    
                    # Get current (config) value display (without showing "(none)" since we have the arrow)
                    config_display = variable.get_display_value(mask_sensitive=True, max_length=15, show_none=False)
                    if not config_display:  # If still empty after show_none=False, show actual value
                        config_display = str(variable.value) if variable.value else "(empty)"
                    
                    # Highlight the arrow and config value in bold yellow to show it's a custom override
                    default_val = f"{orig_display} [bold yellow]{IconManager.arrow_right()} {config_display}[/bold yellow]"
                else:
                    # Use variable's native get_display_value() method (shows "(none)" for empty)
                    default_val = variable.get_display_value(mask_sensitive=True, max_length=30, show_none=True)
                
                # Add lock icon for sensitive variables
                sensitive_icon = f" {IconManager.lock()}" if variable.sensitive else ""
                var_display = f"  {var_name}{sensitive_icon}"

                variables_table.add_row(
                    var_display,
                    variable.type or "str",
                    default_val,
                    variable.description or "",
                    style=row_style,
                )

        console.print(variables_table)

    def display_file_generation_confirmation(
        self, 
        output_dir: Path, 
        files: dict[str, str], 
        existing_files: list[Path] | None = None
    ) -> None:
        """Display files to be generated with confirmation prompt."""
        console.print()
        console.print("[bold]Files to be generated:[/bold]")
        
        def get_file_generation_info(file_path_str):
            file_path = Path(file_path_str)
            file_name = file_path.parts[-1] if file_path.parts else file_path.name
            full_path = output_dir / file_path
            
            if existing_files and full_path in existing_files:
                return (file_path, file_name, 'yellow', '[red](will overwrite)[/red]')
            else:
                return (file_path, file_name, 'green', None)
        
        file_tree = self._build_file_tree(
            f"{IconManager.folder()} [cyan]{output_dir.resolve()}[/cyan]",
            files.keys(),
            get_file_generation_info
        )
        
        console.print(file_tree)
        console.print()

    def display_config_tree(self, spec: dict, module_name: str, show_all: bool = False) -> None:
        """Display configuration spec as a tree view.
        
        Args:
            spec: The configuration spec dictionary
            module_name: Name of the module
            show_all: If True, show all details including descriptions
        """
        if not spec:
            console.print(f"[yellow]No configuration found for module '{module_name}'[/yellow]")
            return

        # Create root tree node
        tree = Tree(f"[bold blue]{IconManager.config()} {str.capitalize(module_name)} Configuration[/bold blue]")

        for section_name, section_data in spec.items():
            if not isinstance(section_data, dict):
                continue

            # Determine if this is a section with variables
            # Guard against None from empty YAML sections
            section_vars = section_data.get("vars") or {}
            section_desc = section_data.get("description", "")
            section_required = section_data.get("required", False)
            section_toggle = section_data.get("toggle", None)
            section_needs = section_data.get("needs", None)

            # Build section label
            section_label = f"[cyan]{section_name}[/cyan]"
            if section_required:
                section_label += " [yellow](required)[/yellow]"
            if section_toggle:
                section_label += f" [dim](toggle: {section_toggle})[/dim]"
            if section_needs:
                needs_str = ", ".join(section_needs) if isinstance(section_needs, list) else section_needs
                section_label += f" [dim](needs: {needs_str})[/dim]"
            
            if show_all and section_desc:
                section_label += f"\n  [dim]{section_desc}[/dim]"

            section_node = tree.add(section_label)

            # Add variables
            if section_vars:
                for var_name, var_data in section_vars.items():
                    if isinstance(var_data, dict):
                        var_type = var_data.get("type", "string")
                        var_default = var_data.get("default", "")
                        var_desc = var_data.get("description", "")
                        var_sensitive = var_data.get("sensitive", False)

                        # Build variable label
                        var_label = f"[green]{var_name}[/green] [dim]({var_type})[/dim]"
                        
                        if var_default is not None and var_default != "":
                            display_val = "********" if var_sensitive else str(var_default)
                            if not var_sensitive and len(display_val) > 30:
                                display_val = display_val[:27] + "..."
                            var_label += f" = [yellow]{display_val}[/yellow]"
                        
                        if show_all and var_desc:
                            var_label += f"\n    [dim]{var_desc}[/dim]"
                        
                        section_node.add(var_label)
                    else:
                        # Simple key-value pair
                        section_node.add(f"[green]{var_name}[/green] = [yellow]{var_data}[/yellow]")

        console.print(tree)

    def display_next_steps(self, next_steps: str, variable_values: dict) -> None:
        """Display next steps after template generation, rendering them as a Jinja2 template.
        
        Args:
            next_steps: The next_steps string from template metadata (may contain Jinja2 syntax)
            variable_values: Dictionary of variable values to use for rendering
        """
        if not next_steps:
            return
        
        console.print("\n[bold cyan]Next Steps:[/bold cyan]")
        
        try:
            from jinja2 import Template as Jinja2Template
            next_steps_template = Jinja2Template(next_steps)
            rendered_next_steps = next_steps_template.render(variable_values)
            console.print(rendered_next_steps)
        except Exception as e:
            logger.warning(f"Failed to render next_steps as template: {e}")
            # Fallback to plain text if rendering fails
            console.print(next_steps)
