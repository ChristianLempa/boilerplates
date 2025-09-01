from typing import Dict, Any
from ...core.variables import BaseVariables


class ComposeVariables(BaseVariables):
    """Compose-specific variable sets declaration.

    Each entry in `variable_sets` is now a mapping with a `prompt` to ask
    whether the set should be applied and a `variables` mapping containing
    the individual variable definitions.
    """

    variable_sets: Dict[str, Dict[str, Any]] = {
        "general": {
            "always": True,
            "prompt": "Do you want to change the general settings?",
            "variables": {
                    "service_name": {"display_name": "Service name", "default": None, "type": "str", "prompt": "Enter service name"},
                    "service_port": {
                        "display_name": "Service port",
                        "type": "int",
                        "prompt": "Enter service port(s)",
                    },
                    "container_name": {"display_name": "Container name", "default": "", "type": "str", "prompt": "Enter container name"},
                    "docker_network": {"display_name": "Docker network", "default": "bridge", "type": "str", "prompt": "Enter Docker network name"},
            },
        },
        "swarm": {
            "prompt_enable": "Do you want to enable swarm mode?",
            "prompt": "Do you want to change the Swarm settings?",
            "variables": {
                "swarm_replicas": {"display_name": "Number of replicas", "default": 1, "type": "int", "prompt": "Enter number of replicas"},
            },
        },
        "traefik": {
            "prompt_enable": "Do you want to add Traefik labels?",
            "prompt": "Do you want to change the Traefik labels?",
            "variables": {
                "traefik_enable": {"display_name": "Enable Traefik", "default": True, "type": "bool", "prompt": "Enable Traefik routing for this service?"},
                "traefik_host": {"display_name": "Routing Rule Host", "default": "", "type": "str", "prompt": "Enter hostname for the routing rule (e.g., example.com))"},
                "traefik_tls": {"display_name": "Enable TLS", "default": True, "type": "bool", "prompt": "Enable TLS for this router?"},
                "traefik_certresolver": {"display_name": "Certificate resolver", "default": "cloudflare", "type": "str", "prompt": "Enter certificate resolver name"},
                "traefik_middleware": {"display_name": "Middlewares", "default": "", "type": "str", "prompt": "Enter middlewares (comma-separated, leave empty for none)"},
            },
        },
    }
