from collections import OrderedDict

from ..core.module import Module
from ..core.registry import registry

spec = OrderedDict(
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
          "container_hostname": {
            "description": "Container internal hostname",
            "type": "str",
            "default": "",
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
          }
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
        "prompt": "Enable Docker Swarm deployment?",
        "toggle": "swarm_enabled",
        "description": "Deploy service in Docker Swarm mode with replicas.",
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
      "database": {
        "title": "Database",
        "prompt": "Configure external database connection?",
        "toggle": "database_enabled",
        "description": "Connect to external database (PostgreSQL, MySQL, MariaDB, etc.)",
        "vars": {
          "database_enabled": {
            "description": "Enable external database integration",
            "type": "bool",
            "default": False,
          },
          "database_type": {
            "description": "Database type",
            "type": "enum",
            "options": ["postgres", "mysql", "mariadb", "sqlite"],
            "default": "postgres",
          },
          "database_host": {
            "description": "Database host",
            "type": "str",
            "default": "database",
          },
          "database_port": {
            "description": "Database port",
            "type": "int",
            "default": 5432,
          },
          "database_name": {
            "description": "Database name",
            "type": "str",
            "default": "",
          },
          "database_user": {
            "description": "Database user",
            "type": "str",
            "default": "",
          },
          "database_password": {
            "description": "Database password",
            "type": "str",
            "default": "",
          },
        },
      },
      "email": {
        "title": "Email Server",
        "prompt": "Configure email server for notifications and user management?",
        "toggle": "email_enabled",
        "description": "Used for notifications, sign-ups, password resets, and alerts.",
        "vars": {
          "email_enabled": {
            "description": "Enable email server configuration",
            "type": "bool",
            "default": False,
          },
          "email_host": {
            "description": "SMTP server hostname",
            "type": "str",
            "default": "",
          },
          "email_port": {
            "description": "SMTP server port",
            "type": "int",
            "default": 587,
          },
          "email_username": {
            "description": "SMTP username",
            "type": "str",
            "default": "",
          },
          "email_password": {
            "description": "SMTP password",
            "type": "str",
            "default": "",
          },
          "email_from": {
            "description": "From email address",
            "type": "str",
            "default": "",
          },
          "email_use_tls": {
            "description": "Use TLS encryption",
            "type": "bool",
            "default": True,
          },
          "email_use_ssl": {
            "description": "Use SSL encryption",
            "type": "bool",
            "default": False,
          },
        },
      },
    }
  )


class ComposeModule(Module):
  """Docker Compose module."""

  name = "compose"
  description = "Manage Docker Compose configurations"
  files = ["compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"]


registry.register(ComposeModule)
