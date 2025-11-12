"""Docker Compose module with multi-schema support."""

from typing import Annotated

from typer import Option

from ...core.module import Module
from ...core.module.base_commands import validate_templates
from ...core.registry import registry

# Import schema specifications
from .spec_v1_0 import spec as spec_1_0
from .spec_v1_1 import spec as spec_1_1
from .spec_v1_2 import spec as spec_1_2
from .validate import run_docker_validation

# Schema version mapping
SCHEMAS = {
    "1.0": spec_1_0,
    "1.1": spec_1_1,
    "1.2": spec_1_2,
}

# Default spec points to latest version
spec = spec_1_2


class ComposeModule(Module):
    """Docker Compose module with extended validation."""

    name = "compose"
    description = "Manage Docker Compose configurations"
    schema_version = "1.2"  # Current schema version supported by this module
    schemas = SCHEMAS  # Available schema versions

    def validate(  # noqa: PLR0913
        self,
        template_id: str | None = None,
        path: str | None = None,
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
        """
        # Run standard validation first
        validate_templates(self, template_id, path, verbose, semantic)

        # If docker validation is enabled and we have a specific template
        if docker and (template_id or path):
            run_docker_validation(self, template_id, path, docker_test_all, verbose)


registry.register(ComposeModule)
