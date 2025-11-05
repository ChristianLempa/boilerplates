#!/usr/bin/env python3
"""
Main entry point for the Boilerplates CLI application.
This file serves as the primary executable when running the CLI.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
import sys
from pathlib import Path

import click
from rich.console import Console
from typer import Option, Typer
from typer.core import TyperGroup

import cli.modules
from cli import __version__
from cli.core import repo
from cli.core.display import DisplayManager
from cli.core.registry import registry


class OrderedGroup(TyperGroup):
    """Typer Group that lists commands in alphabetical order."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(super().list_commands(ctx))


app = Typer(
    help=(
        "CLI tool for managing infrastructure boilerplates.\n\n"
        "[dim]Easily generate, customize, and deploy templates for Docker Compose, "
        "Terraform, Kubernetes, and more.\n\n "
        "[white]Made with 💜 by [bold]Christian Lempa[/bold]"
    ),
    add_completion=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=False,
    no_args_is_help=True,
    cls=OrderedGroup,
)
console = Console()
display = DisplayManager()


def setup_logging(log_level: str = "WARNING") -> None:
    """Configure the logging system with the specified log level.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Raises:
        ValueError: If the log level is invalid
        RuntimeError: If logging configuration fails
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level '{log_level}'. Valid levels: DEBUG, INFO, WARNING, ERROR, CRITICAL")

    try:
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        logger = logging.getLogger(__name__)
        logger.setLevel(numeric_level)
    except Exception as e:
        raise RuntimeError(f"Failed to configure logging: {e}") from e


@app.callback(invoke_without_command=True)
def main(
    _version: bool | None = Option(
        None,
        "--version",
        "-v",
        help="Show the application version and exit.",
        is_flag=True,
        callback=lambda v: console.print(f"boilerplates version {__version__}") or sys.exit(0) if v else None,
        is_eager=True,
    ),
    log_level: str | None = Option(
        None,
        "--log-level",
        help=("Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). If omitted, logging is disabled."),
    ),
) -> None:
    """CLI tool for managing infrastructure boilerplates."""
    # Disable logging by default; only enable when user provides --log-level
    if log_level:
        # Re-enable logging and configure
        logging.disable(logging.NOTSET)
        setup_logging(log_level)
    else:
        # Silence all logging (including third-party) unless user explicitly requests it
        logging.disable(logging.CRITICAL)

    # Get context without type annotation (compatible with all Typer versions)
    ctx = click.get_current_context()

    # Store log level in context for potential use by other commands
    ctx.ensure_object(dict)
    ctx.obj["log_level"] = log_level

    # If no subcommand is provided, show help and friendly intro
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        sys.exit(0)


def _import_modules(modules_path: Path, logger: logging.Logger) -> list[str]:
    """Import all modules and return list of failures."""
    failed_imports = []
    for _finder, name, ispkg in pkgutil.iter_modules([str(modules_path)]):
        if not name.startswith("_") and name != "base":
            try:
                logger.debug(f"Importing module: {name} ({'package' if ispkg else 'file'})")
                importlib.import_module(f"cli.modules.{name}")
            except ImportError as e:
                error_info = f"Import failed for '{name}': {e!s}"
                failed_imports.append(error_info)
                logger.warning(error_info)
            except Exception as e:
                error_info = f"Unexpected error importing '{name}': {e!s}"
                failed_imports.append(error_info)
                logger.error(error_info)
    return failed_imports


def _register_repo_command(logger: logging.Logger) -> list[str]:
    """Register repo command and return list of failures."""
    failed = []
    try:
        logger.debug("Registering repo command")
        repo.register_cli(app)
    except Exception as e:
        error_info = f"Repo command registration failed: {e!s}"
        failed.append(error_info)
        logger.warning(error_info)
    return failed


def _register_module_classes(logger: logging.Logger) -> tuple[list, list[str]]:
    """Register template-based modules and return (module_classes, failures)."""
    failed_registrations = []
    module_classes = list(registry.iter_module_classes())
    logger.debug(f"Registering {len(module_classes)} template-based modules")

    for _name, module_cls in module_classes:
        try:
            logger.debug(f"Registering module class: {module_cls.__name__}")
            module_cls.register_cli(app)
        except Exception as e:
            error_info = f"Registration failed for '{module_cls.__name__}': {e!s}"
            failed_registrations.append(error_info)
            logger.warning(error_info)
            display.warning(error_info)

    return module_classes, failed_registrations


def _build_error_details(failed_imports: list[str], failed_registrations: list[str]) -> str:
    """Build detailed error message from failures."""
    error_details = []
    if failed_imports:
        error_details.extend(["Import failures:"] + [f"  - {err}" for err in failed_imports])
    if failed_registrations:
        error_details.extend(["Registration failures:"] + [f"  - {err}" for err in failed_registrations])
    return "\n".join(error_details) if error_details else ""


def init_app() -> None:
    """Initialize the application by discovering and registering modules.

    Raises:
        ImportError: If critical module import operations fail
        RuntimeError: If application initialization fails
    """
    logger = logging.getLogger(__name__)
    failed_imports = []
    failed_registrations = []

    try:
        # Auto-discover and import all modules
        modules_path = Path(cli.modules.__file__).parent
        logger.debug(f"Discovering modules in {modules_path}")
        failed_imports = _import_modules(modules_path, logger)

        # Register core repo command
        repo_failures = _register_repo_command(logger)

        # Register template-based modules
        module_classes, failed_registrations = _register_module_classes(logger)
        failed_registrations.extend(repo_failures)

        # Validate we have modules
        if not module_classes and not failed_imports:
            raise RuntimeError("No modules found to register")

        # Log summary
        successful_modules = len(module_classes) - len(failed_registrations)
        logger.info(f"Application initialized: {successful_modules} modules registered successfully")
        if failed_imports:
            logger.info(f"Module import failures: {len(failed_imports)}")
        if failed_registrations:
            logger.info(f"Module registration failures: {len(failed_registrations)}")

    except Exception as e:
        details = _build_error_details(failed_imports, failed_registrations) or str(e)
        raise RuntimeError(f"Application initialization failed: {details}") from e


def run() -> None:
    """Run the CLI application."""
    # Configure logging early if --log-level is provided
    if "--log-level" in sys.argv:
        try:
            log_level_index = sys.argv.index("--log-level") + 1
            if log_level_index < len(sys.argv):
                log_level = sys.argv[log_level_index]
                logging.disable(logging.NOTSET)
                setup_logging(log_level)
        except (ValueError, IndexError):
            pass  # Let Typer handle argument parsing errors

    try:
        init_app()
        app()
    except (ValueError, RuntimeError) as e:
        # Handle configuration and initialization errors cleanly
        display.error(str(e))
        sys.exit(1)
    except ImportError as e:
        # Handle module import errors with detailed info
        display.error(f"Module Import Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        display.warning("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        # Handle unexpected errors - show simplified message
        display.error(str(e))
        display.info("Use --log-level DEBUG for more details")
        sys.exit(1)


if __name__ == "__main__":
    run()
