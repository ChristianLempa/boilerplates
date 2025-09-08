from ..core.module import Module
from ..core.registry import registry

class ComposeModule(Module):
  """Docker Compose module."""
  
  name = "compose"
  description = "Manage Docker Compose configurations"
  files = ["docker-compose.yml", "compose.yml", "compose.yaml"]
  
  # Category metadata
  categories = {
    "general": {
      "icon": "󰖷 ",
      "description": "General container settings"
    },
    "network": {
      "icon": "󰈀 ",
      "description": "Network configuration",
      "tip": "Use external networks for cross-container communication"
    },
    "traefik": {
      "icon": " ",
      "description": "Reverse proxy and load balancer",
      "tip": "Automatic SSL certificates with Let's Encrypt"
    },
    "swarm": {
      "icon": " ",
      "description": "Docker Swarm orchestration"
    }
  }
  
  # Variable metadata
  variable_metadata = {
    "service_name": {
      "hint": "e.g., webapp, api, database",
      "validation": "^[a-z][a-z0-9-]*$"
    },
    "container_name": {
      "hint": "Leave empty to use service name",
      "description": "Custom container name"
    },
    "network": {
      "description": "Enable custom network configuration"
    },
    "network.name": {
      "hint": "e.g., frontend, backend, bridge",
      "description": "Docker network name"
    },
    "network.external": {
      "hint": "Use 'true' for existing networks",
      "tip": "External networks must be created before running"
    },
    "traefik": {
      "description": "Enable Traefik reverse proxy",
      "tip": "Requires Traefik to be running separately"
    },
    "traefik.host": {
      "hint": "e.g., app.example.com, api.mydomain.org",
      "description": "Domain name for your service",
      "validation": "^[a-z0-9][a-z0-9.-]*[a-z0-9]$"
    },
    "traefik.tls": {
      "description": "Enable HTTPS/TLS",
      "tip": "Requires valid domain and DNS configuration"
    },
    "traefik.certresolver": {
      "hint": "e.g., letsencrypt, staging",
      "description": "Certificate resolver name"
    },
    "swarm": {
      "description": "Enable Docker Swarm mode",
      "tip": "Requires Docker Swarm to be initialized"
    },
    "swarm.replicas": {
      "hint": "Number of container instances",
      "validation": "^[1-9][0-9]*$"
    },
    "service_port_http": {
      "hint": "e.g., 8080, 3000, 80",
      "description": "HTTP port mapping",
      "validation": "^[1-9][0-9]{0,4}$"
    },
    "service_port_https": {
      "hint": "e.g., 8443, 3443, 443",
      "description": "HTTPS port mapping",
      "validation": "^[1-9][0-9]{0,4}$"
    },
    "nginx_dashboard": {
      "description": "Enable Nginx status dashboard"
    },
    "nginx_dashboard_port_dashboard": {
      "hint": "e.g., 8081, 9090",
      "description": "Dashboard port",
      "validation": "^[1-9][0-9]{0,4}$"
    }
  }

# Register the module
registry.register(ComposeModule)
