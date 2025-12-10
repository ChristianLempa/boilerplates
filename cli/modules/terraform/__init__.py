"""Terraform module with multi-schema support."""

import logging
from collections import OrderedDict

from ...core.module import Module
from ...core.registry import registry
from ...core.schema import has_schema, list_versions, load_schema

logger = logging.getLogger(__name__)


def _load_json_spec_as_dict(version: str) -> OrderedDict:
    """Load JSON schema and convert to dict format for backward compatibility.

    Args:
        version: Schema version

    Returns:
        OrderedDict in the same format as Python specs
    """
    logger.debug(f"Loading terraform schema {version} from JSON")
    json_spec = load_schema("terraform", version)

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
        if not has_schema("terraform", version):
            raise KeyError(
                f"Schema version {version} not found for terraform module. "
                f"Available: {', '.join(list_versions('terraform'))}"
            )
        return _load_json_spec_as_dict(version)

    def __contains__(self, version):
        return has_schema("terraform", version)


# Initialize schema dict
SCHEMAS = _SchemaDict()

# Default spec - load latest version
spec = _load_json_spec_as_dict("1.0")


class TerraformModule(Module):
    """Terraform module."""

    name = "terraform"
    description = "Manage Terraform configurations"
    schema_version = "1.0"  # Current schema version supported by this module
    schemas = SCHEMAS  # Available schema versions


registry.register(TerraformModule)
