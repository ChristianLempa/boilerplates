"""Helm module schema version 1.0 - Original specification."""

from collections import OrderedDict

spec = OrderedDict(
    {
        "general": {
            "title": "General",
            "vars": {
                "release_name": {
                    "description": "Helm release name",
                    "type": "str",
                },
            },
        },
    }
)
