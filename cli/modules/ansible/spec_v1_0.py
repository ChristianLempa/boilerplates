"""Ansible module schema version 1.0 - Original specification."""

from collections import OrderedDict

spec = OrderedDict(
    {
        "general": {
            "title": "General",
            "required": True,
            "vars": {
                "playbook_name": {
                    "description": "Ansible playbook name",
                    "type": "str",
                },
                "target_hosts": {
                    "description": "Target hosts pattern (e.g., 'all', 'webservers', or '{{ my_hosts | d([]) }}')",
                    "type": "str",
                    "default": "{{ my_hosts | d([]) }}",
                },
                "become": {
                    "description": "Run tasks with privilege escalation (sudo)",
                    "type": "bool",
                    "default": False,
                },
            },
        },
        "options": {
            "title": "Options",
            "toggle": "options_enabled",
            "vars": {
                "options_enabled": {
                    "description": "Enable additional playbook options",
                    "type": "bool",
                    "default": False,
                },
                "gather_facts": {
                    "description": "Gather facts about target hosts",
                    "type": "bool",
                    "default": True,
                },
            },
        },
        "secrets": {
            "title": "Secrets",
            "toggle": "secrets_enabled",
            "vars": {
                "secrets_enabled": {
                    "description": "Use external secrets file",
                    "type": "bool",
                    "default": False,
                },
                "secrets_file": {
                    "description": "Path to secrets file",
                    "type": "str",
                    "default": "secrets.yaml",
                },
            },
        },
    }
)
