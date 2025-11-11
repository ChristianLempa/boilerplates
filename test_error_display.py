#!/usr/bin/env python3
"""Interactive test script to see clean error display in action."""

from cli.core.display import DisplayManager
from cli.core.exceptions import RenderErrorContext, TemplateRenderError


def show_header():
    """Show template header like in real generation."""
    print("┏" + "━" * 78 + "┓")
    print("┃ Nginx (id:nginx │ version:1.25.3 │ schema:1.1 │ library: default)     " + " " * 18 + "┃")
    print("┗" + "━" * 78 + "┛")
    print()
    print("Nginx web server template with reverse proxy support.")
    print()
    print("Template File Structure")
    print()
    print(" nginx")
    print("├──  compose.yaml")
    print("└──  .env")
    print()


def scenario_1_template_error():
    """Scenario 1: Template rendering error with file location."""
    display = DisplayManager()

    print("\n" + "=" * 80)
    print("SCENARIO 1: Template Render Error (with file location)")
    print("=" * 80 + "\n")

    show_header()
    print("Customize any settings? [y/n] (n): n")

    # Create error with context
    context = RenderErrorContext(file_path="compose.yaml.j2", line_number=25)
    error = TemplateRenderError("Undefined variable 'missing_var'", context=context)

    # Display clean error
    display.text("")
    display.text("─" * 80, style="dim")
    display.text("")

    details = error.file_path
    if error.line_number:
        details += f":line {error.line_number}"

    display.error("Failed to generate boilerplate from template 'nginx'", details=details)


def scenario_2_permission_error():
    """Scenario 2: File permission error."""
    display = DisplayManager()

    print("\n\n" + "=" * 80)
    print("SCENARIO 2: File Permission Error")
    print("=" * 80 + "\n")

    show_header()
    print("Customize any settings? [y/n] (n): n")
    print()
    print(" Warning: Directory '/protected/path' is not empty. 2 file(s) will be overwritten.")
    print()
    print("Continue? [y/n] (n): y")

    # Display error
    display.text("")
    display.text("─" * 80, style="dim")
    display.text("")

    error_msg = "[Errno 13] Permission denied: '/protected/path/compose.yaml'"
    display.error("Failed to generate boilerplate from template 'nginx'", details=error_msg)


def scenario_3_validation_error():
    """Scenario 3: Long validation error (truncated)."""
    display = DisplayManager()

    print("\n\n" + "=" * 80)
    print("SCENARIO 3: Validation Error (truncated)")
    print("=" * 80 + "\n")

    show_header()
    print("Customize any settings? [y/n] (n): n")

    # Display error
    display.text("")
    display.text("─" * 80, style="dim")
    display.text("")

    error_msg = "Template validation failed: services.nginx.ports configuration is invalid. Expected a list of port mappings but got a string. Please check your Docker Compose syntax."
    if len(error_msg) > 100:
        error_msg = error_msg[:100] + "..."

    display.error("Failed to generate boilerplate from template 'nginx'", details=error_msg)


def scenario_4_success_comparison():
    """Scenario 4: Show successful generation for comparison."""
    display = DisplayManager()

    print("\n\n" + "=" * 80)
    print("SCENARIO 4: Successful Generation (for comparison)")
    print("=" * 80 + "\n")

    show_header()
    print("Customize any settings? [y/n] (n): n")

    # Display success
    display.text("")
    display.text("─" * 80, style="dim")

    display.success("Boilerplate generated successfully in 'nginx'")


if __name__ == "__main__":
    print("\nThis script demonstrates the clean error display formatting.")
    print("Pay attention to the separator line, error icon, and details formatting.\n")

    input("Press ENTER to see Scenario 1 (Template Error with file location)...")
    scenario_1_template_error()

    input("\n\nPress ENTER to see Scenario 2 (Permission Error)...")
    scenario_2_permission_error()

    input("\n\nPress ENTER to see Scenario 3 (Long Validation Error)...")
    scenario_3_validation_error()

    input("\n\nPress ENTER to see Scenario 4 (Success for comparison)...")
    scenario_4_success_comparison()

    print("\n\n" + "=" * 80)
    print("All scenarios complete!")
    print("=" * 80 + "\n")
