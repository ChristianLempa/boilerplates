"""Docker Compose module with multi-schema support."""

import logging
from collections import OrderedDict
from typing import Annotated

from typer import Argument, Option

from ...core.module import Module
from ...core.module.base_commands import validate_templates
from ...core.registry import registry
from ...core.schema import has_schema, list_versions, load_schema
from .validate import run_docker_validation

logger = logging.getLogger(__name__)


def _load_json_spec_as_dict(version: str) -> OrderedDict:
    """Load JSON schema and convert to dict format for backward compatibility.

    Args:
        version: Schema version

    Returns:
        OrderedDict in the same format as Python specs
    """
    logger.debug(f"Loading compose schema {version} from JSON")
    json_spec = load_schema("compose", version)

    # Convert JSON array format to OrderedDict format
    spec_dict = OrderedDict()
    for section_data in json_spec:
        section_key = section_data["key"]

        # Build section dict
        section_dict = {}
        if "title" in section_data:
            section_dict["title"] = section_data["title"]
        if "description" in section_data:
            section_dict["description"] = section_data["description"]
        if "toggle" in section_data:
            section_dict["toggle"] = section_data["toggle"]
        if "required" in section_data:
            section_dict["required"] = section_data["required"]
        if "needs" in section_data:
            section_dict["needs"] = section_data["needs"]

        # Convert vars array to dict
        vars_dict = OrderedDict()
        for var_data in section_data["vars"]:
            var_name = var_data["name"]
            var_dict = {k: v for k, v in var_data.items() if k != "name"}
            vars_dict[var_name] = var_dict

        section_dict["vars"] = vars_dict
        spec_dict[section_key] = section_dict

    return spec_dict


# Schema version mapping - loads JSON schemas on-demand
class _SchemaDict(dict):
    """Dict subclass that loads JSON schemas on-demand."""

    def __getitem__(self, version):
        if not has_schema("compose", version):
            raise KeyError(
                f"Schema version {version} not found for compose module. "
                f"Available: {', '.join(list_versions('compose'))}"
            )
        return _load_json_spec_as_dict(version)

    def __contains__(self, version):
        return has_schema("compose", version)


# Initialize schema dict
SCHEMAS = _SchemaDict()

# Default spec - load latest version
spec = _load_json_spec_as_dict("1.2")


class ComposeModule(Module):
    """Docker Compose module with extended validation."""

    name = "compose"
    description = "Manage Docker Compose configurations"
    schema_version = "1.2"  # Current schema version supported by this module
    schemas = SCHEMAS  # Available schema versions

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
