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
                help="Enable semantic validation (Docker Compose config, YAML structure, etc.)",
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
        """Validate Compose templates."""
        validate_templates(self, template_id, path, verbose, semantic)

        if docker and (template_id or path):
            run_docker_validation(self, template_id, path, docker_test_all, verbose)


registry.register(ComposeModule)
