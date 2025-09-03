from typing import Dict, Any
from ...core.variables import BaseVariables


class ComposeVariables(BaseVariables):
    """Compose-specific variable sets declaration.

    Each entry in `variable_sets` is now a mapping with a `prompt` to ask
    whether the set should be applied and a `variables` mapping containing
    the individual variable definitions.
    """

    def __init__(self) -> None:
        self.variable_sets: Dict[str, Dict[str, Any]] = {
        "general": {
            "always": True,
            "prompt": "Do you want to change the general settings?",
            "variables": {
                    "service_name": {"display_name": "Service name", "default": None, "type": "str", "prompt": "Enter service name"},
                    "service_port": {"display_name": "Service port", "default": None, "type": "int", "prompt": "Enter service port(s)", "description": "Port number(s) the service will expose (has to be a single port)"},
                    "container_name": {"display_name": "Container name", "default": None, "type": "str", "prompt": "Enter container name"},
                    "container_hostname": {"display_name": "Container hostname", "default": None, "type": "str", "prompt": "Enter container hostname", "description": "Hostname that will be set inside the container"},
                    "docker_network": {"display_name": "Docker network", "default": "bridge", "type": "str", "prompt": "Enter Docker network name"},
                    "restart_policy": {"display_name": "Restart policy", "default": "unless-stopped", "type": "str", "prompt": "Enter restart policy"},
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
                "traefik_host": {"display_name": "Routing Rule Host", "default": None, "type": "str", "prompt": "Enter hostname for the routing rule (e.g., example.com))", "description": "Domain name that Traefik will use to route traffic to this service"},
                "traefik_tls": {"display_name": "Enable TLS", "default": False, "type": "bool", "prompt": "Enable TLS for this router?", "description": "Whether to enable HTTPS/TLS encryption for this route"},
                "traefik_certresolver": {"display_name": "Certificate resolver", "type": "str", "prompt": "Enter certificate resolver name", "description": "Name of the certificate resolver to use for obtaining SSL certificates"},
                "traefik_middleware": {"display_name": "Middlewares", "default": None, "type": "str", "prompt": "Enter middlewares (comma-separated, leave empty for none)", "description": "Comma-separated list of Traefik middlewares to apply to this route"},
                "traefik_entrypoint": {"display_name": "EntryPoint", "default": "web", "type": "str", "prompt": "Enter entrypoint name", "description": "Name of the Traefik entrypoint to use for this router"},
            },
        },
    }
        super().__init__()
