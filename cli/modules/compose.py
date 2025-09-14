from ..core.module import Module
from ..core.registry import registry


class ComposeModule(Module):
  """Docker Compose module."""
  
  name = "compose"
  description = "Manage Docker Compose configurations"
  files = ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]

  variables_spec = {
    # Root
    "service_name": {"type": "str", "display": "Service Name", "description": "Service name"},
    "container_name": {"type": "str", "display": "Container Name", "description": "Custom container name (leave empty to use service name)"},
    "container_timezone": {"type": "str", "display": "Container Timezone", "description": "Container timezone (e.g., Europe/Berlin, America/New_York)"},
    "container_loglevel": {"type": "enum", "display": "Log Level", "description": "Container log level", "default": "info", "options": ["debug", "info", "warn", "error"]},
    "container_hostname": {"type": "str", "display": "Container Hostname", "description": "Container hostname (shows up in logs and networking)"},
    "restart_policy": {"type": "enum", "display": "Restart Policy", "description": "Container restart policy", "default": "unless-stopped", "options": ["unless-stopped", "always", "on-failure", "no"]},

    # Ports
    "ports": {"type": "bool", "display": "Enable Ports", "description": "Enable port mapping"},

    # Network
    "network": {"type": "bool", "display": "Enable Network", "description": "Enable custom network configuration"},
    "network.name": {"type": "str", "display": "Network Name", "description": "Docker network name (e.g., frontend, backend, bridge)", "default": "bridge"},
    "network.external": {"type": "bool", "display": "External Network", "description": "Use existing network (must be created before running)"},

    # Traefik
    "traefik": {"type": "bool", "display": "Enable Traefik", "description": "Enable Traefik reverse proxy (requires Traefik to be running separately)"},
    "traefik.host": {"type": "hostname", "display": "Host Domain", "description": "Domain name for your service (e.g., app.example.com)"},
    "traefik.entrypoint": {"type": "str", "display": "HTTP Entrypoint", "description": "HTTP entrypoint for non-TLS traffic (e.g., web, http)", "default": "web"},
    "traefik.tls": {"type": "bool", "display": "Enable TLS", "description": "Enable HTTPS/TLS (requires valid domain and DNS configuration)"},
    "traefik.tls.entrypoint": {"type": "str", "display": "TLS Entrypoint", "description": "TLS entrypoint for HTTPS traffic (e.g., websecure, https)", "default": "websecure"},
    "traefik.tls.certresolver": {"type": "str", "display": "Cert Resolver", "description": "Certificate resolver name (e.g., letsencrypt, staging)"},

    # PostgreSQL
    "postgres": {"type": "bool", "display": "Enable PostgreSQL", "description": "Enable PostgreSQL database"},
    "postgres.host": {"type": "str", "display": "PostgreSQL Host", "description": "PostgreSQL host (e.g., localhost, postgres, db.example.com)"},

    # Swarm
    "swarm": {"type": "bool", "display": "Enable Swarm", "description": "Enable Docker Swarm mode (requires Docker Swarm to be initialized)"},
    "swarm.replicas": {"type": "int", "display": "Replicas", "description": "Number of container instances", "default": 1},
  }

# Register the module
registry.register(ComposeModule)
