"""Docker Compose module."""

from __future__ import annotations

import logging
from typing import Annotated

from typer import Argument, Option

from ...core.module import Module
from ...core.module.base_commands import ValidationConfig, validate_templates
from ...core.registry import registry
from .validate import ComposeDockerValidator

logger = logging.getLogger(__name__)


class ComposeModule(Module):
    """Docker Compose module with extended validation."""

    name = "compose"
    description = "Manage Docker Compose configurations"
    kind_validator_class = ComposeDockerValidator

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
        all_templates: Annotated[
            bool,
            Option("--all", help="Validate all Compose templates (default when no template ID is provided)"),
        ] = False,
        verbose: Annotated[bool, Option("--verbose", "-v", help="Show detailed validation information")] = False,
        semantic: Annotated[
            bool,
            Option(
                "--semantic/--no-semantic",
                help="Enable semantic validation for rendered files",
            ),
        ] = True,
        matrix: Annotated[
            bool,
            Option(
                "--matrix",
                help="Validate all reachable dependency states for a single template",
            ),
        ] = False,
        kind: Annotated[
            bool,
            Option(
                "--kind",
                help="Enable dependency-matrix Docker Compose validation",
            ),
        ] = False,
        docker: Annotated[
            bool,
            Option(
                "--docker/--no-docker",
                help="Alias for --kind Docker Compose validation",
            ),
        ] = False,
        docker_test_all: Annotated[
            bool,
            Option(
                "--docker-test-all",
                help="Alias for --matrix --kind Docker Compose validation",
            ),
        ] = False,
    ) -> None:
        """Validate Compose templates."""
        kind_enabled = kind or docker or docker_test_all
        matrix_enabled = matrix or docker_test_all
        kind_validator = self.kind_validator_class(verbose).validate_rendered_files if kind_enabled else None
        validate_templates(
            self,
            template_id,
            path,
            ValidationConfig(
                verbose=verbose,
                semantic=semantic,
                matrix=matrix_enabled,
                kind=kind_enabled,
                all_templates=all_templates,
                kind_validator=kind_validator,
            ),
        )


registry.register(ComposeModule)
