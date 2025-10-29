from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from . import DisplayManager
    from ..template import Template

console = Console()


class TemplateDisplayManager:
    """Handles all template-related rendering.

    This manager is responsible for displaying template information,
    file trees, and metadata.
    """

    def __init__(self, parent: "DisplayManager"):
        """Initialize TemplateDisplayManager.

        Args:
            parent: Reference to parent DisplayManager for accessing shared resources
        """
        self.parent = parent

    def render_template(self, template: "Template", template_id: str) -> None:
        """Display template information panel and variables table.

        Args:
            template: Template instance to display
            template_id: ID of the template
        """
        self.render_template_header(template, template_id)
        self.render_file_tree(template)
        self.parent.variables.render_variables_table(template)

    def render_template_header(self, template: "Template", template_id: str) -> None:
        """Display the header for a template with library information.

        Args:
            template: Template instance
            template_id: ID of the template
        """
        settings = self.parent.settings

        template_name = template.metadata.name or settings.TEXT_UNNAMED_TEMPLATE
        version = (
            str(template.metadata.version)
            if template.metadata.version
            else settings.TEXT_VERSION_NOT_SPECIFIED
        )
        schema = (
            template.schema_version if hasattr(template, "schema_version") else "1.0"
        )
        description = template.metadata.description or settings.TEXT_NO_DESCRIPTION

        # Get library information and format with helper
        library_name = template.metadata.library or ""
        library_type = template.metadata.library_type or "git"
        library_display = self.parent._format_library_display(
            library_name, library_type
        )

        console.print(
            f"[{settings.STYLE_HEADER}]{template_name} ({template_id} - [cyan]{version}[/cyan] - [magenta]schema {schema}[/magenta]) {library_display}[/{settings.STYLE_HEADER}]"
        )
        console.print(description)

    def render_file_tree(self, template: "Template") -> None:
        """Display the file structure of a template.

        Args:
            template: Template instance
        """
        from . import IconManager

        settings = self.parent.settings
        console.print()
        console.print(
            f"[{settings.STYLE_HEADER}]Template File Structure:[/{settings.STYLE_HEADER}]"
        )

        def get_template_file_info(template_file):
            display_name = (
                template_file.output_path.name
                if hasattr(template_file, "output_path")
                else template_file.relative_path.name
            )
            return (template_file.relative_path, display_name, "white", None)

        file_tree = self.parent._render_file_tree_internal(
            f"{IconManager.folder()} [white]{template.id}[/white]",
            template.template_files,
            get_template_file_info,
        )

        if file_tree.children:
            console.print(file_tree)

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
        from . import IconManager

        console.print()
        console.print("[bold]Files to be generated:[/bold]")

        def get_file_generation_info(file_path_str):
            file_path = Path(file_path_str)
            file_name = file_path.parts[-1] if file_path.parts else file_path.name
            full_path = output_dir / file_path

            if existing_files and full_path in existing_files:
                return (file_path, file_name, "yellow", "[red](will overwrite)[/red]")
            else:
                return (file_path, file_name, "green", None)

        file_tree = self.parent._render_file_tree_internal(
            f"{IconManager.folder()} [cyan]{output_dir.resolve()}[/cyan]",
            files.keys(),
            get_file_generation_info,
        )

        console.print(file_tree)
        console.print()
