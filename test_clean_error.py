#!/usr/bin/env python3
"""Test cleaner error display."""

from cli.core.display import DisplayManager
from cli.core.exceptions import RenderErrorContext, TemplateRenderError


def test_template_render_error():
    """Simulate a clean template rendering error."""
    display = DisplayManager()

    # Show some context before the error
    print("┏" + "━" * 78 + "┓")
    print("┃ Nginx (id:nginx │ version:1.25.3 │ schema:1.1 │ library: default)     " + " " * 18 + "┃")
    print("┗" + "━" * 78 + "┛")
    print()
    print("Nginx web server template.")
    print()
    print("Template File Structure")
    print()
    print(" nginx")
    print("├──  compose.yaml")
    print("└──  .env")
    print()
    print("Customize any settings? [y/n] (n): n")

    # Create error with context
    context = RenderErrorContext(file_path="compose.yaml.j2", line_number=25)
    error = TemplateRenderError("Undefined variable 'missing_var'", context=context)

    # Display using the new clean format
    display.text("")
    display.text("─" * 80, style="dim")
    display.text("")
    display.error("Failed to generate boilerplate from template 'nginx'")
    display.text(f"  {error.file_path}:line {error.line_number}", style="dim")


def test_generic_error():
    """Simulate a clean generic error."""
    display = DisplayManager()

    print("\n\n" + "=" * 80)
    print("SCENARIO 2: File Permission Error")
    print("=" * 80 + "\n")

    # Show some context
    print("Boilerplate generated successfully in '/protected/path'")

    # Display error
    error_msg = "[Errno 13] Permission denied: '/protected/path/compose.yaml'"

    display.text("")
    display.text("─" * 80, style="dim")
    display.text("")
    display.error("Failed to generate boilerplate from template 'nginx'")
    display.text(f"  {error_msg}", style="dim")


def test_long_error():
    """Simulate error with long message that gets truncated."""
    display = DisplayManager()

    print("\n\n" + "=" * 80)
    print("SCENARIO 3: Long Error Message (truncated)")
    print("=" * 80 + "\n")

    error_msg = "Template validation failed: services.nginx.ports configuration is invalid. Expected a list of port mappings but got a string. Please check your Docker Compose syntax and ensure ports are defined as a list."

    if len(error_msg) > 100:
        error_msg = error_msg[:100] + "..."

    display.text("")
    display.text("─" * 80, style="dim")
    display.text("")
    display.error("Failed to generate boilerplate from template 'nginx'")
    display.text(f"  {error_msg}", style="dim")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SCENARIO 1: Template Render Error")
    print("=" * 80 + "\n")

    test_template_render_error()
    test_generic_error()
    test_long_error()

    print("\n")
