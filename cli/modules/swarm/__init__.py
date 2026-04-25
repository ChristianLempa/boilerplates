"""Docker Swarm module with compose-compatible validation."""

import logging
from typing import Annotated

from typer import Argument, Option

from ...core.module import Module
from ...core.module.base_commands import ValidationConfig, validate_templates
from ...core.registry import registry
from ..compose.validate import ComposeDockerValidator

logger = logging.getLogger(__name__)


class SwarmModule(Module):
    """Docker Swarm module."""

    name = "swarm"
    description = "Manage Docker Swarm stack templates"
    kind_validator_class = ComposeDockerValidator

    def validate(  # noqa: PLR0913
        self,
        template_id: Annotated[
            str | None,
            Argument(help="Template ID to validate"),
        ] = None,
        *,
        path: Annotated[
            str | None,
            Option("--path", help="Path to template directory for validation"),
        ] = None,
        all_templates: Annotated[
            bool,
            Option("--all", help="Validate all Swarm templates"),
        ] = False,
        verbose: Annotated[bool, Option("--verbose", "-v", help="Show detailed validation information")] = False,
        semantic: Annotated[
            bool,
            Option(
                "--semantic",
                help="Enable dependency-matrix semantic validation",
            ),
        ] = False,
        kind: Annotated[
            bool,
            Option(
                "--kind",
                help="Enable dependency-matrix Docker Compose validation",
            ),
        ] = False,
    ) -> None:
        """Validate Swarm templates."""
        kind_validator = self.kind_validator_class(verbose).validate_rendered_files if kind else None
        validate_templates(
            self,
            template_id,
            path,
            ValidationConfig(
                verbose=verbose,
                semantic=semantic,
                kind=kind,
                all_templates=all_templates,
                kind_validator=kind_validator,
            ),
        )


registry.register(SwarmModule)
