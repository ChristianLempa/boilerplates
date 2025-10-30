"""Packer module schema version 1.0 - Original specification."""

from collections import OrderedDict

spec = OrderedDict(
    {
        "general": {
            "title": "General",
            "vars": {
                "image_name": {
                    "description": "Image name",
                    "type": "str",
                },
            },
        },
    }
)
