"""Terraform module schema version 1.0 - Original specification."""

from collections import OrderedDict

spec = OrderedDict(
    {
        "general": {
            "title": "General",
            "vars": {
                "resource_name": {
                    "description": "Resource name prefix",
                    "type": "str",
                },
                "backend_mode": {
                    "description": "Terraform backend mode",
                    "type": "enum",
                    "options": ["local", "http"],
                    "default": "local",
                },
            },
        },
    }
)
