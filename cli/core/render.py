"""
Core rendering functionality for handling template output and display.
Provides consistent rendering and output handling across different module types.
"""
import logging
from pathlib import Path
from typing import Optional, Union

from rich.console import Console
from rich.syntax import Syntax

logger = logging.getLogger(__name__)

class RenderOutput:
    """Handles the output of rendered templates."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        
    def write_to_file(self, content: str, output_path: Path) -> None:
        """
        Write rendered content to a file.
        
        Args:
            content: Content to write
            output_path: Path to write the content to
            
        Raises:
            Exception: If writing fails
        """
        try:
            # Ensure parent directory exists
            output_parent = output_path.parent
            if not output_parent.exists():
                output_parent.mkdir(parents=True, exist_ok=True)
                
            output_path.write_text(content, encoding="utf-8")
            self.console.print(f"[green]Rendered content written to {output_path}[/green]")
        except Exception as e:
            raise Exception(f"Failed to write output to {output_path}: {e}")
            
    def print_to_console(self, content: str, syntax: str = "yaml",
                        template_name: Optional[str] = None) -> None:
        """
        Print rendered content to the console with syntax highlighting.
        
        Args:
            content: Content to print
            syntax: Syntax highlighting to use (default: yaml)
            template_name: Optional template name to show in header
        """
        if template_name:
            self.console.print(f"\n\nGenerated Content for [bold cyan]{template_name}[/bold cyan]\n")
            
        syntax_output = Syntax(
            content,
            syntax,
            theme="monokai",
            line_numbers=False,
            word_wrap=True
        )
        self.console.print(syntax_output)
        
    def output_rendered_content(self, content: str, output_target: Optional[Union[str, Path]],
                              syntax: str = "yaml", template_name: Optional[str] = None) -> None:
        """
        Output rendered content either to a file or console.
        
        Args:
            content: Content to output
            output_target: Path to output file or None for console output
            syntax: Syntax highlighting to use for console output
            template_name: Optional template name for console output header
            
        Raises:
            Exception: If writing to file fails
        """
        if output_target:
            if isinstance(output_target, str):
                output_target = Path(output_target)
            self.write_to_file(content, output_target)
        else:
            self.print_to_console(content, syntax, template_name)
