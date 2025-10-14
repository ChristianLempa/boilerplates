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
console_err = Console(stderr=True)


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
    UI_LIBRARY_GIT = "\uf418"       #  (git icon)
    UI_LIBRARY_STATIC = "\uf07c"    #  (folder icon)
    
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
    """Handles all rich rendering for the CLI.
    
    This class is responsible for ALL display output in the CLI, including:
    - Status messages (success, error, warning, info)
    - Tables (templates, summaries, results)
    - Trees (file structures, configurations)
    - Confirmation dialogs and prompts
    - Headers and sections
    
    Design Principles:
    - All display logic should go through DisplayManager methods
    - IconManager is ONLY used internally by DisplayManager
    - External code should never directly call IconManager or console.print
    - Consistent formatting across all display types
    """
    
    def __init__(self, quiet: bool = False):
        """Initialize DisplayManager.
        
        Args:
            quiet: If True, suppress all non-error output
        """
        self.quiet = quiet

    def display_templates_table(
        self, templates: list, module_name: str, title: str
    ) -> None:
        """Display a table of templates with library type indicators.
        
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
            
            # Show library with type indicator and color
            library_name = template.metadata.library or ""
            library_type = template.metadata.library_type or "git"
            
            if library_type == "static":
                # Static libraries: yellow/amber color with folder icon
                library_display = f"[yellow]{IconManager.UI_LIBRARY_STATIC} {library_name}[/yellow]"
            else:
                # Git libraries: blue color with git icon
                library_display = f"[blue]{IconManager.UI_LIBRARY_GIT} {library_name}[/blue]"
            
            # Display qualified ID if present (e.g., "alloy.default")
            display_id = template.id

            table.add_row(display_id, name, tags, version, library_display)

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
        # Errors and warnings always go to stderr, even in quiet mode
        # Success and info respect quiet mode and go to stdout
        if level in ('error', 'warning'):
            output_console = console_err
            should_print = True
        else:
            output_console = console
            should_print = not self.quiet
        
        if not should_print:
            return
        
        icon = IconManager.get_status_icon(level)
        colors = {'error': 'red', 'warning': 'yellow', 'success': 'green', 'info': 'blue'}
        color = colors.get(level, 'white')
        
        # Format message based on context
        if context:
            text = f"{level.capitalize()} in {context}: {message}" if level == 'error' or level == 'warning' else f"{context}: {message}"
        else:
            text = f"{level.capitalize()}: {message}" if level == 'error' or level == 'warning' else message
        
        output_console.print(f"[{color}]{icon} {text}[/{color}]")
        
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
        """Display the header for a template with library information."""
        template_name = template.metadata.name or "Unnamed Template"
        version = str(template.metadata.version) if template.metadata.version else "Not specified"
        description = template.metadata.description or "No description available"
        
        # Get library information
        library_name = template.metadata.library or ""
        library_type = template.metadata.library_type or "git"
        
        # Format library display with icon and color
        if library_type == "static":
            library_display = f"[yellow]{IconManager.UI_LIBRARY_STATIC} {library_name}[/yellow]"
        else:
            library_display = f"[blue]{IconManager.UI_LIBRARY_GIT} {library_name}[/blue]"

        console.print(
            f"[bold blue]{template_name} ({template_id} - [cyan]{version}[/cyan]) {library_display}[/bold blue]"
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
                # Add required indicator for required variables
                required_indicator = " [yellow](required)[/yellow]" if variable.required else ""
                var_display = f"  {var_name}{sensitive_icon}{required_indicator}"

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
    
    def display_status_table(self, title: str, rows: list[tuple[str, str, bool]], 
                            columns: tuple[str, str] = ("Item", "Status")) -> None:
        """Display a status table with success/error indicators.
        
        Args:
            title: Table title
            rows: List of tuples (name, message, success_bool)
            columns: Column headers (name_header, status_header)
        """
        table = Table(title=title, show_header=True)
        table.add_column(columns[0], style="cyan", no_wrap=True)
        table.add_column(columns[1])
        
        for name, message, success in rows:
            status_style = "green" if success else "red"
            status_icon = IconManager.get_status_icon("success" if success else "error")
            table.add_row(name, f"[{status_style}]{status_icon} {message}[/{status_style}]")
        
        console.print(table)
    
    def display_summary_table(self, title: str, items: dict[str, str]) -> None:
        """Display a simple two-column summary table.
        
        Args:
            title: Table title
            items: Dictionary of key-value pairs to display
        """
        table = Table(title=title, show_header=False, box=None, padding=(0, 2))
        table.add_column(style="bold")
        table.add_column()
        
        for key, value in items.items():
            table.add_row(key, value)
        
        console.print(table)
    
    def display_file_operation_table(self, files: list[tuple[str, int, str]]) -> None:
        """Display a table of file operations with sizes and statuses.
        
        Args:
            files: List of tuples (file_path, size_bytes, status)
        """
        table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))
        table.add_column("File", style="white", no_wrap=False)
        table.add_column("Size", justify="right", style="dim")
        table.add_column("Status", style="yellow")
        
        for file_path, size_bytes, status in files:
            # Format size
            if size_bytes < 1024:
                size_str = f"{size_bytes}B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f}KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f}MB"
            
            table.add_row(str(file_path), size_str, status)
        
        console.print(table)
    
    def display_heading(self, text: str, icon_type: str | None = None, style: str = "bold") -> None:
        """Display a heading with optional icon.
        
        Args:
            text: Heading text
            icon_type: Type of icon to display (e.g., 'folder', 'file', 'config')
            style: Rich style to apply
        """
        if icon_type:
            icon = self._get_icon_by_type(icon_type)
            console.print(f"[{style}]{icon} {text}[/{style}]")
        else:
            console.print(f"[{style}]{text}[/{style}]")
    
    def display_warning_with_confirmation(self, message: str, details: list[str] | None = None, 
                                         default: bool = False) -> bool:
        """Display a warning message with optional details and get confirmation.
        
        Args:
            message: Warning message to display
            details: Optional list of detail lines to show
            default: Default value for confirmation
            
        Returns:
            True if user confirms, False otherwise
        """
        icon = IconManager.get_status_icon('warning')
        console.print(f"\n[yellow]{icon} {message}[/yellow]")
        
        if details:
            for detail in details:
                console.print(f"[yellow]  {detail}[/yellow]")
        
        from rich.prompt import Confirm
        return Confirm.ask("Continue?", default=default)
    
    def display_skipped(self, message: str, reason: str | None = None) -> None:
        """Display a skipped/disabled message.
        
        Args:
            message: The main message to display
            reason: Optional reason why it was skipped
        """
        icon = IconManager.get_status_icon('skipped')
        if reason:
            console.print(f"\n[dim]{icon} {message} (skipped - {reason})[/dim]")
        else:
            console.print(f"\n[dim]{icon} {message} (skipped)[/dim]")
    
    def get_lock_icon(self) -> str:
        """Get the lock icon for sensitive variables.
        
        Returns:
            Lock icon unicode character
        """
        return IconManager.lock()
    
    def _get_icon_by_type(self, icon_type: str) -> str:
        """Get icon by semantic type name.
        
        Args:
            icon_type: Type of icon (e.g., 'folder', 'file', 'config', 'lock')
            
        Returns:
            Icon unicode character
        """
        icon_map = {
            'folder': IconManager.folder(),
            'file': IconManager.FILE_DEFAULT,
            'config': IconManager.config(),
            'lock': IconManager.lock(),
            'arrow': IconManager.arrow_right(),
        }
        return icon_map.get(icon_type, '')
    
    def display_template_render_error(self, error: 'TemplateRenderError', context: str | None = None) -> None:
        """Display a detailed template rendering error with context and suggestions.
        
        Args:
            error: TemplateRenderError exception with detailed error information
            context: Optional context information (e.g., template ID)
        """
        from rich.panel import Panel
        from rich.syntax import Syntax
        
        # Always display errors to stderr
        # Display main error header
        icon = IconManager.get_status_icon('error')
        if context:
            console_err.print(f"\n[red bold]{icon} Template Rendering Error[/red bold] [dim]({context})[/dim]")
        else:
            console_err.print(f"\n[red bold]{icon} Template Rendering Error[/red bold]")
        
        console_err.print()
        
        # Display error message
        if error.file_path:
            console_err.print(f"[red]Error in file:[/red] [cyan]{error.file_path}[/cyan]")
            if error.line_number:
                location = f"Line {error.line_number}"
                if error.column:
                    location += f", Column {error.column}"
                console_err.print(f"[red]Location:[/red] {location}")
        
        console_err.print(f"[red]Message:[/red] {str(error.original_error) if error.original_error else str(error)}")
        console_err.print()
        
        # Display code context if available
        if error.context_lines:
            console_err.print("[bold cyan]Code Context:[/bold cyan]")
            
            # Build the context text
            context_text = "\n".join(error.context_lines)
            
            # Display in a panel with syntax highlighting if possible
            file_ext = Path(error.file_path).suffix if error.file_path else ""
            if file_ext == ".j2":
                # Remove .j2 to get base extension for syntax highlighting
                base_name = Path(error.file_path).stem
                base_ext = Path(base_name).suffix
                lexer = "jinja2" if not base_ext else None
            else:
                lexer = None
            
            try:
                if lexer:
                    syntax = Syntax(context_text, lexer, line_numbers=False, theme="monokai")
                    console_err.print(Panel(syntax, border_style="red", padding=(1, 2)))
                else:
                    console_err.print(Panel(context_text, border_style="red", padding=(1, 2)))
            except Exception:
                # Fallback to plain panel if syntax highlighting fails
                console_err.print(Panel(context_text, border_style="red", padding=(1, 2)))
            
            console_err.print()
        
        # Display suggestions if available
        if error.suggestions:
            console_err.print("[bold yellow]Suggestions:[/bold yellow]")
            for i, suggestion in enumerate(error.suggestions, 1):
                bullet = IconManager.UI_BULLET
                console_err.print(f"  [yellow]{bullet}[/yellow] {suggestion}")
            console_err.print()
        
        # Display variable context in debug mode
        if error.variable_context:
            console_err.print("[bold blue]Available Variables (Debug):[/bold blue]")
            var_list = ", ".join(sorted(error.variable_context.keys()))
            console_err.print(f"[dim]{var_list}[/dim]")
            console_err.print()
