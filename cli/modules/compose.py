from ..core.module import Module
from ..core.variables import Variable
from ..core.registry import registry

class ComposeModule(Module):
  """Docker Compose module with variables."""
  
  name = "compose"
  description = "Manage Docker Compose configurations"
  files = ["docker-compose.yml", "compose.yml", "compose.yaml"]
  
  def _init_variables(self):
    """Initialize Compose-specific variables."""
    # Register groups
    self.variables.register_group(
      "general", "General Settings",
      "Basic configuration for Docker Compose services"
    )
    
    self.variables.register_group(
      "traefik", "Traefik Configuration", 
      "Reverse proxy settings", icon="󰞉", enabler="traefik"
    )
    
    # Register variables
    self.variables.register_variable(Variable(
      name="service_name",
      description="Name of the service",
      group="general",
      required=True
    ))
    
    self.variables.register_variable(Variable(
      name="container_name",
      description="Container name",
      group="general"
    ))
    
    self.variables.register_variable(Variable(
      name="traefik",
      description="Enable Traefik",
      type="boolean",
      default=False,
      group="traefik"
    ))
    
    self.variables.register_variable(Variable(
      name="traefik_host",
      description="Traefik hostname",
      default=None,
      group="traefik"
    ))

# Register the module
registry.register(ComposeModule)
