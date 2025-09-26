from collections import OrderedDict

from ..core.module import Module
from ..core.registry import registry


class ComposeModule(Module):
  """Docker Compose module."""

  name = "compose"
  description = "Manage Docker Compose configurations"
  files = ["compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"]

  variable_sections = OrderedDict(
    {
      "general": {
        "title": "General",
        "vars": {
          "service_name": {
            "description": "Service name",
            "type": "str",
            "default": "",
          },
          "container_name": {
            "description": "Container name",
            "type": "str",
            "default": "",
          },
          "container_timezone": {
            "description": "Container timezone (e.g., Europe/Berlin)",
            "type": "str",
            "default": "UTC",
          },
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
        },
      },
      "network": {
        "title": "Network",
        "prompt": "Enable custom network block?",
        "toggle": "network_enabled",
        "vars": {
          "network_enabled": {
            "description": "Enable custom network block",
            "type": "bool",
            "default": False,
          },
          "network_name": {
            "description": "Docker network name",
            "type": "str",
            "default": "bridge",
          },
          "network_external": {
            "description": "Use existing Docker network",
            "type": "bool",
            "default": True,
          },
        },
      },
      "ports": {
        "title": "Ports",
        "prompt": "Expose ports via 'ports' mapping?",
        "toggle": "ports_enabled",
        "vars": {
          "ports_enabled": {
            "description": "Expose ports via 'ports' mapping",
            "type": "bool",
            "default": False,
          },
          "service_port_http": {
            "description": "HTTP service port (host)",
            "type": "int",
            "default": 8080,
          },
          "service_port_https": {
            "description": "HTTPS service port (host)",
            "type": "int",
            "default": 8443,
          },
          "ports_http": {
            "description": "Port for HTTP access to the service",
            "type": "int",
            "default": 5678,
          },
        },
      },
      "traefik": {
        "title": "Traefik",
        "prompt": "Enable Traefik reverse proxy integration?",
        "toggle": "traefik_enabled",
        "description": "Traefik routes external traffic to your service.",
        "vars": {
          "traefik_enabled": {
            "description": "Enable Traefik reverse proxy integration",
            "type": "bool",
            "default": False,
          },
          "traefik_host": {
            "description": "Domain name for your service",
            "type": "hostname",
            "default": "",
          },
          "traefik_entrypoint": {
            "description": "HTTP entrypoint (non-TLS)",
            "type": "str",
            "default": "web",
          },
          "traefik_tls_enabled": {
            "description": "Enable HTTPS/TLS",
            "type": "bool",
            "default": True,
          },
          "traefik_tls_entrypoint": {
            "description": "TLS entrypoint",
            "type": "str",
            "default": "websecure",
          },
          "traefik_tls_certresolver": {
            "description": "Traefik certificate resolver name",
            "type": "str",
            "default": "",
          },
        },
      },
      "swarm": {
        "title": "Docker Swarm",
        "vars": {
          "swarm_enabled": {
            "description": "Enable Docker Swarm mode",
            "type": "bool",
            "default": False,
          },
          "swarm_replicas": {
            "description": "Number of replicas in Swarm",
            "type": "int",
            "default": 1,
          },
        },
      },
      "nginx": {
        "title": "Nginx Dashboard",
        "vars": {
          "nginx_dashboard_enabled": {
            "description": "Enable Nginx dashboard",
            "type": "bool",
            "default": False,
          },
          "nginx_dashboard_port": {
            "description": "Nginx dashboard port (host)",
            "type": "int",
            "default": 8081,
          },
        },
      },
      "postgres": {
        "title": "PostgreSQL",
        "prompt": "Configure external PostgreSQL database?",
        "toggle": "postgres_enabled",
        "vars": {
          "postgres_enabled": {
            "description": "Enable PostgreSQL integration",
            "type": "bool",
            "default": False,
          },
          "postgres_host": {
            "description": "PostgreSQL host",
            "type": "str",
            "default": "postgres",
          },
          "postgres_port": {
            "description": "PostgreSQL port",
            "type": "int",
            "default": 5432,
          },
          "postgres_database": {
            "description": "PostgreSQL database name",
            "type": "str",
            "default": "",
          },
          "postgres_user": {
            "description": "PostgreSQL user",
            "type": "str",
            "default": "",
          },
          "postgres_password": {
            "description": "PostgreSQL password",
            "type": "str",
            "default": "",
          },
        },
      },
    }
  )


registry.register(ComposeModule)
