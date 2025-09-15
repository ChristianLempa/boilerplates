from ..core.module import Module
from ..core.registry import registry


class ComposeModule(Module):
  """Docker Compose module.

  Flat variable names only. Simple, explicit toggles (e.g., traefik_enabled) instead of dotted sections.
  """

  name = "compose"
  description = "Manage Docker Compose configurations"
  # Per rule: prefer compose.yaml first, legacy names kept as fallback
  files = ["compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"]

  # Common Compose variables used across templates. Only variables actually used
  # in a given template are kept during merge.
  variables_spec = {
    # General
    "service_name": {"description": "Service name", "type": "str"},
    "container_name": {"description": "Container name", "type": "str"},
    "container_timezone": {"description": "Container timezone (e.g., Europe/Berlin)", "type": "str"},
    "container_loglevel": {
      "description": "Container log level",
      "type": "enum",
      "options": ["debug", "info", "warn", "error"],
      "default": "info",
    },
    "restart_policy": {
      "description": "Container restart policy",
      "type": "enum",
      "options": ["unless-stopped", "always", "on-failure", "no"],
      "default": "unless-stopped",
    },

    # Networking
    "network_enabled": {"description": "Enable custom network block", "type": "bool", "default": False},
    "network_name": {"description": "Docker network name", "type": "str", "default": "bridge"},
    "network_external": {"description": "Use existing Docker network", "type": "bool", "default": True},

    # Ports
    "ports_enabled": {"description": "Expose ports via 'ports' mapping", "type": "bool", "default": False},
    "service_port_http": {"description": "HTTP service port (host)", "type": "int", "default": 8080},
    "service_port_https": {"description": "HTTPS service port (host)", "type": "int", "default": 8443},

    # Traefik
    "traefik_enabled": {"description": "Enable Traefik reverse proxy integration", "type": "bool", "default": False},
    "traefik_host": {"description": "Domain name for your service", "type": "hostname"},
    "traefik_entrypoint": {"description": "HTTP entrypoint (non-TLS)", "type": "str", "default": "web"},
    "traefik_tls_enabled": {"description": "Enable HTTPS/TLS", "type": "bool", "default": True},
    "traefik_tls_entrypoint": {"description": "TLS entrypoint", "type": "str", "default": "websecure"},
    "traefik_tls_certresolver": {"description": "Traefik certificate resolver name", "type": "str"},

    # Docker Swarm
    "swarm_enabled": {"description": "Enable Docker Swarm mode", "type": "bool", "default": False},
    "swarm_replicas": {"description": "Number of replicas in Swarm", "type": "int", "default": 1},

    # Nginx example
    "nginx_dashboard_enabled": {"description": "Enable Nginx dashboard", "type": "bool", "default": False},
    "nginx_dashboard_port": {"description": "Nginx dashboard port (host)", "type": "int", "default": 8081},

    # PostgreSQL integration
    "postgres_enabled": {"description": "Enable PostgreSQL integration", "type": "bool", "default": False},
    "postgres_host": {"description": "PostgreSQL host", "type": "str", "default": "postgres"},
    "postgres_port": {"description": "PostgreSQL port", "type": "int", "default": 5432},
    "postgres_database": {"description": "PostgreSQL database name", "type": "str"},
    "postgres_user": {"description": "PostgreSQL user", "type": "str"},
    "postgres_password": {"description": "PostgreSQL password", "type": "str"},
  }


# Register the module
registry.register(ComposeModule)
