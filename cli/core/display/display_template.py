from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .display_icons import IconManager
from .display_settings import DisplaySettings

if TYPE_CHECKING:
    from ..template import Template
    from .display_base import BaseDisplay
    from .display_status import StatusDisplay
    from .display_variable import VariableDisplay


class TemplateDisplay:
    """Template-related rendering.

    Provides methods for displaying template information,
    file trees, and metadata.
    """

    def __init__(
        self,
        settings: DisplaySettings,
        base: BaseDisplay,
        variables: VariableDisplay,
        status: StatusDisplay,
    ):
        """Initialize TemplateDisplay.

        Args:
            settings: Display settings for formatting
            base: BaseDisplay instance
            variables: VariableDisplay instance for rendering variables
            status: StatusDisplay instance for markdown rendering
        """
        self.settings = settings
        self.base = base
        self.variables = variables
        self.status = status

    def render_template(self, template: Template, template_id: str) -> None:
        """Display template information panel and variables table.

        Args:
            template: Template instance to display
            template_id: ID of the template
        """
        self.render_template_header(template, template_id)
        self.render_file_tree(template)
        self.variables.render_variables_table(template)

    def render_template_header(self, template: Template, template_id: str) -> None:
        """Display the header for a template with library information.

        Args:
            template: Template instance
            template_id: ID of the template
        """
        settings = self.settings

        template_name = template.metadata.name or settings.TEXT_UNNAMED_TEMPLATE
        version = str(template.metadata.version) if template.metadata.version else settings.TEXT_VERSION_NOT_SPECIFIED
        description = template.metadata.description or settings.TEXT_NO_DESCRIPTION

        # Get library information and format with icon/color
        library_name = template.metadata.library or ""
        library_type = template.metadata.library_type or "git"
        icon = IconManager.UI_LIBRARY_STATIC if library_type == "static" else IconManager.UI_LIBRARY_GIT
        color = "yellow" if library_type == "static" else "blue"

        # Create custom H1-style header with Rich markup support

        # Build header content with Rich formatting
        header_content = Text()
        header_content.append(template_name, style="bold white")
        header_content.append(" (", style="white")
        header_content.append("id:", style="white")
        header_content.append(template_id, style="dim")
        header_content.append(" │ ", style="dim")
        header_content.append("version:", style="white")
        header_content.append(version, style="cyan")
        header_content.append(" │ ", style="dim")
        header_content.append("library:", style="white")
        header_content.append(icon + " ", style=color)
        header_content.append(library_name, style=color)
        header_content.append(")", style="white")

        panel = Panel(header_content, box=box.HEAVY, style="markdown.h1.border")
        Console().print(panel)
        self.base.text("")
        self.status.markdown(description)

    def render_file_tree(self, template: Template) -> None:
        """Display the file structure of a template.

        Args:
            template: Template instance
        """
        self.base.text("")
        self.base.heading("Template File Structure")

        def get_template_file_info(template_file):
            display_name = (
                template_file.output_path.name
                if hasattr(template_file, "output_path")
                else template_file.relative_path.name
            )
            return (template_file.relative_path, display_name, "white", None)

        if template.template_files:
            self.base.file_tree(
                f"{IconManager.folder()} [white]{template.id}[/white]",
                template.template_files,
                get_template_file_info,
            )

    def render_file_generation_confirmation(
        self,
        output_dir: Path,
        files: dict[str, str],
        existing_files: list[Path] | None = None,
    ) -> None:
        """Display files to be generated with confirmation prompt.

        Args:
            output_dir: Output directory path
            files: Dictionary of file paths to content
            existing_files: List of existing files that will be overwritten
        """
        self.base.text("")
        self.base.heading("Files to be Generated")

        def get_file_generation_info(file_path_str):
            file_path = Path(file_path_str)
            file_name = file_path.parts[-1] if file_path.parts else file_path.name
            full_path = output_dir / file_path

            if existing_files and full_path in existing_files:
                return (file_path, file_name, "yellow", "[red](will overwrite)[/red]")
            return (file_path, file_name, "green", None)

        self.base.file_tree(
            f"{IconManager.folder()} [cyan]{output_dir.resolve()}[/cyan]",
            files.keys(),
            get_file_generation_info,
        )
        self.base.text("")
