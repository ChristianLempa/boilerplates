"""Docker Compose module."""

import logging
from typing import Annotated

from typer import Argument, Option

from ...core.module import Module
from ...core.module.base_commands import validate_templates
from ...core.registry import registry
from .validate import run_docker_validation

logger = logging.getLogger(__name__)


class ComposeModule(Module):
    """Docker Compose module with extended validation."""

    name = "compose"
    description = "Manage Docker Compose configurations"

    def validate(  # noqa: PLR0913
        self,
        template_id: Annotated[
            str | None,
            Argument(help="Template ID to validate (omit to validate all templates)"),
        ] = None,
        *,
        path: Annotated[
            str | None,
            Option("--path", help="Path to template directory for validation"),
        ] = None,
        verbose: Annotated[bool, Option("--verbose", "-v", help="Show detailed validation information")] = False,
        semantic: Annotated[
            bool,
            Option(
                "--semantic/--no-semantic",
                help="Enable semantic validation (Docker Compose schema, etc.)",
            ),
        ] = True,
        docker: Annotated[
            bool,
            Option(
                "--docker/--no-docker",
                help="Enable Docker Compose validation using 'docker compose config'",
            ),
        ] = False,
        docker_test_all: Annotated[
            bool,
            Option(
                "--docker-test-all",
                help="Test all variable combinations (minimal, maximal, each toggle). Requires --docker",
            ),
        ] = False,
    ) -> None:
        """Validate templates for Jinja2 syntax, undefined variables, and semantic correctness.

        Extended for Docker Compose with optional docker compose config validation.
        Use --docker for single config test, --docker-test-all for comprehensive testing.

        Examples:
            # Validate specific template
            compose validate netbox

            # Validate all templates
            compose validate

            # Validate with Docker Compose config check
            compose validate netbox --docker
        """
        # Run standard validation first
        validate_templates(self, template_id, path, verbose, semantic)

        # If docker validation is enabled and we have a specific template
        if docker and (template_id or path):
            run_docker_validation(self, template_id, path, docker_test_all, verbose)


registry.register(ComposeModule)
