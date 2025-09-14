from ..core.module import Module
from ..core.registry import registry
from ..core.variables import Variable, VariableRegistry, VariableType

class ComposeModule(Module):
  """Docker Compose module."""
  
  name = "compose"
  description = "Manage Docker Compose configurations"
  files = ["docker-compose.yml", "compose.yml", "compose.yaml"]
  
  def _init_variables(self):
    """Initialize module-specific variables."""
    self.variables = VariableRegistry()
    
    # Register root variables
    self.variables.register_variable(Variable(
      name="service_name",
      type=VariableType.STR,
      description="Service name",
      display="Service Name"
    ))
    
    self.variables.register_variable(Variable(
      name="container_name",
      type=VariableType.STR,
      description="Custom container name (leave empty to use service name)",
      display="Container Name"
    ))
    
    self.variables.register_variable(Variable(
      name="container_timezone",
      type=VariableType.STR,
      description="Container timezone (e.g., Europe/Berlin, America/New_York)",
      display="Container Timezone"
    ))
    
    self.variables.register_variable(Variable(
      name="container_loglevel",
      type=VariableType.ENUM,
      description="Container log level",
      display="Log Level",
      default="info",
      options=["debug", "info", "warn", "error"]
    ))
    
    self.variables.register_variable(Variable(
      name="container_hostname",
      type=VariableType.STR,
      description="Container hostname (shows up in logs and networking)",
      display="Container Hostname"
    ))
    
    self.variables.register_variable(Variable(
      name="restart_policy",
      type=VariableType.ENUM,
      description="Container restart policy",
      display="Restart Policy",
      default="unless-stopped",
      options=["unless-stopped", "always", "on-failure", "no"]
    ))
    
    self.variables.register_variable(Variable(
      name="ports",
      type=VariableType.BOOL,
      description="Enable port mapping",
      display="Enable Ports"
    ))
    
    # Network variables
    self.variables.register_variable(Variable(
      name="network",
      type=VariableType.BOOL,
      description="Enable custom network configuration",
      display="Enable Network"
    ))
    
    self.variables.register_variable(Variable(
      name="name",
      type=VariableType.STR,
      description="Docker network name (e.g., frontend, backend, bridge)",
      display="Network Name",
      default="bridge",
      parent="network"
    ))
    
    self.variables.register_variable(Variable(
      name="external",
      type=VariableType.BOOL,
      description="Use existing network (must be created before running)",
      display="External Network",
      parent="network"
    ))
    
    # Traefik variables
    self.variables.register_variable(Variable(
      name="traefik",
      type=VariableType.BOOL,
      description="Enable Traefik reverse proxy (requires Traefik to be running separately)",
      display="Enable Traefik"
    ))
    
    self.variables.register_variable(Variable(
      name="host",
      type=VariableType.STR,
      description="Domain name for your service (e.g., app.example.com)",
      display="Host Domain",
      parent="traefik"
    ))
    
    self.variables.register_variable(Variable(
      name="entrypoint",
      type=VariableType.STR,
      description="HTTP entrypoint for non-TLS traffic (e.g., web, http)",
      display="HTTP Entrypoint",
      default="web",
      parent="traefik"
    ))
    
    self.variables.register_variable(Variable(
      name="tls",
      type=VariableType.BOOL,
      description="Enable HTTPS/TLS (requires valid domain and DNS configuration)",
      display="Enable TLS",
      parent="traefik"
    ))
    
    self.variables.register_variable(Variable(
      name="entrypoint",
      type=VariableType.STR,
      description="TLS entrypoint for HTTPS traffic (e.g., websecure, https)",
      display="TLS Entrypoint",
      default="websecure",
      parent="traefik.tls"
    ))
    
    self.variables.register_variable(Variable(
      name="certresolver",
      type=VariableType.STR,
      description="Certificate resolver name (e.g., letsencrypt, staging)",
      display="Cert Resolver",
      parent="traefik.tls"
    ))
    
    # PostgreSQL variables
    self.variables.register_variable(Variable(
      name="postgres",
      type=VariableType.BOOL,
      description="Enable PostgreSQL database",
      display="Enable PostgreSQL"
    ))
    
    self.variables.register_variable(Variable(
      name="host",
      type=VariableType.STR,
      description="PostgreSQL host (e.g., localhost, postgres, db.example.com)",
      display="PostgreSQL Host",
      parent="postgres"
    ))
    
    # Docker Swarm variables
    self.variables.register_variable(Variable(
      name="swarm",
      type=VariableType.BOOL,
      description="Enable Docker Swarm mode (requires Docker Swarm to be initialized)",
      display="Enable Swarm"
    ))
    
    self.variables.register_variable(Variable(
      name="replicas",
      type=VariableType.INT,
      description="Number of container instances",
      display="Replicas",
      default=1,
      parent="swarm"
    ))

# Register the module
registry.register(ComposeModule)
