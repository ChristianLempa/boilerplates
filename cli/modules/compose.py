from ..core.module import Module
from ..core.variables import VariableGroup, Variable, VariableManager
from ..core.registry import register_module

@register_module(
  name="compose",
  description="Manage Docker Compose configurations and services",
  files=["docker-compose.yml", "compose.yml", "docker-compose.yaml", "compose.yaml"]
)
class ComposeModule(Module):
  """Module for managing Compose configurations and services."""

  def __init__(self):
    # name, description, and files are automatically injected by the decorator!
    vars = self._init_vars()
    super().__init__(name=self.name, description=self.description, files=self.files, vars=vars)

  def _init_vars(self):
    """Initialize default variables for the compose module."""
    
    # Define variable sets configuration as a dictionary
    variable_sets_config = {
      "general": {
        "description": "General variables for compose services",
        "vars": {
          "service_name": {"description": "Name of the service", "value": None},
          "container_name": {"description": "Name of the container", "value": None},
          "docker_image": {"description": "Docker image to use", "value": "nginx:latest"},
          "restart_policy": {"description": "Restart policy", "value": "unless-stopped"}
        }
      },
      "swarm": {
        "description": "Variables for Docker Swarm deployment",
        "vars": {
          "replica_count": {"description": "Number of replicas in Swarm", "value": 1, "var_type": "integer"}
        }
      },
      "traefik": {
        "description": "Variables for Traefik labels",
        "vars": {
          "traefik_http_port": {"description": "HTTP port for Traefik", "value": 80, "var_type": "integer"},
          "traefik_https_port": {"description": "HTTPS port for Traefik", "value": 443, "var_type": "integer"},
          "traefik_entrypoints": {"description": "Entry points for Traefik", "value": ["http", "https"], "var_type": "list"}
        }
      }
    }

    # Convert dictionary configuration to VariableGroup objects using from_dict
    return [VariableGroup.from_dict(name, config) for name, config in variable_sets_config.items()]

  def register(self, app):
    return super().register(app)
