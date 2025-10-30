"""Kubernetes module schema version 1.0 - Original specification."""

from collections import OrderedDict

spec = OrderedDict(
    {
        "general": {
            "title": "General",
            "vars": {
                "namespace": {
                    "description": "Kubernetes namespace",
                    "type": "str",
                    "default": "default",
                },
            },
        },
    }
)
