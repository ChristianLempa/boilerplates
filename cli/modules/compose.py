from ..core.module import Module
from ..core.variables import Variable
from ..core.registry import registry

class ComposeModule(Module):
  """Docker Compose module with variables."""
  
  name = "compose"
  description = "Manage Docker Compose configurations"
  files = ["docker-compose.yml", "compose.yml", "compose.yaml"]
  
  def _init_variables(self):
    """Initialize Compose-specific variables with dotted notation."""
    # General standalone variables - register first
    self.variables.register(Variable(
      name="service_name",
      description="Name of the service"
    ))
    
    self.variables.register(Variable(
      name="container_name",
      description="Container name"
    ))
    
    # Variable for dynamic port mappings (dict type auto-detected from template)
    self.variables.register(Variable(
      name="service_port",
      description="Service port mappings"
    ))
    
    # Network group - enabler controls whether to use network
    self.variables.register(Variable(
      name="network",
      description="Enable custom network",
      type="boolean",
      default=False
    ))
    
    self.variables.register(Variable(
      name="network.name",
      description="Docker network name",
      default="bridge"
    ))
    
    self.variables.register(Variable(
      name="network.external",
      description="Is network external",
      type="boolean",
      default=True
    ))
    
    # Traefik group - enabler controls whether to use Traefik
    self.variables.register(Variable(
      name="traefik",
      description="Enable Traefik reverse proxy",
      type="boolean",
      default=False
    ))
    
    self.variables.register(Variable(
      name="traefik.host",
      description="Hostname for Traefik routing"
    ))
    
    self.variables.register(Variable(
      name="traefik.tls",
      description="Enable TLS",
      type="boolean",
      default=True
    ))

    self.variables.register(Variable(
      name="traefik.certresolver",
      description="Certificate resolver name",
      default="letsencrypt"
    ))
    
    # Swarm group - enabler controls whether to use Swarm mode
    self.variables.register(Variable(
      name="swarm",
      description="Enable Docker Swarm mode",
      type="boolean",
      default=False
    ))
    
    self.variables.register(Variable(
      name="swarm.replicas",
      description="Number of replicas in swarm mode",
      type="integer",
      default=1
    ))

# Register the module
registry.register(ComposeModule)
