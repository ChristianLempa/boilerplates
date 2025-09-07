from ..core.module import Module
from ..core.registry import registry
from ..core.variables import Variable

class TerraformModule(Module):
  """Terraform module - clean and simple."""
  
  name = "terraform"
  description = "Manage Terraform configurations"
  files = ["main.tf", "variables.tf", "outputs.tf", "versions.tf"]
  
  def _init_variables(self):
    """Initialize Terraform-specific variables."""
    # Only if module needs variables
    pass

# Register the module
registry.register(TerraformModule)
