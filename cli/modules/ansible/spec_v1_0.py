"""Ansible module schema version 1.0 - Original specification."""

from collections import OrderedDict

spec = OrderedDict(
    {
        "general": {
            "title": "General",
            "vars": {
                "playbook_name": {
                    "description": "Ansible playbook name",
                    "type": "str",
                },
            },
        },
    }
)
