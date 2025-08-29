#!/usr/bin/env python3
"""
Main entry point for the Boilerplates CLI application.
This file serves as the primary executable when running the CLI.
"""

from cli.core.app import create_app


def main() -> None:
    """Main entry point for the CLI application."""
    app = create_app()
    app()


if __name__ == "__main__":
    main()
