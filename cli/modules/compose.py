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
      "swarm", "Docker Swarm Settings",
      "Settings for deploying services in Docker Swarm mode", icon="󰒋 ", enabler="swarm"
    )

    self.variables.register_group(
      "traefik", "Traefik Configuration", 
      "Reverse proxy settings", icon="󰞉 ", enabler="traefik"
    )
    
    # Register variables
    self.variables.register_variable(Variable(
      name="service_name",
      description="Name of the service",
      group="general"
    ))
    
    self.variables.register_variable(Variable(
      name="container_name",
      description="Container name",
      group="general"
    ))

    self.variables.register_variable(Variable(
      name="service_port",
      description="Port(s) the service listens on (can be single or multiple)",
      type="integer",
      group="general",
      multivalue=True
    ))

    self.variables.register_variable(Variable(
      name="swarm",
      description="Enable Docker Swarm mode",
      type="boolean",
      default=False,
      group="swarm"
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
      group="traefik"
    ))

    self.variables.register_variable(Variable(
      name="traefik_certresolver",
      description="Traefik certificate resolver",
      group="traefik"
    ))
    
    # Add docker_network as a multivalue example
    self.variables.register_variable(Variable(
      name="docker_network",
      description="Docker network(s) to connect to",
      type="string",
      group="general",
      multivalue=True
    ))

# Register the module
registry.register(ComposeModule)
