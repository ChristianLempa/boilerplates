"""
Modules package for the Boilerplates CLI.

To add a new module:
1. Create a new Python file: cli/modules/[module_name].py
2. Create a class inheriting from Module with the import: from ..core.module import Module
3. Ensure the class properly sets 'files' parameter and implements required methods
4. Import and register the module in cli/__main__.py

Available modules:
- compose: Manage Docker Compose configurations and services
- ansible: Manage Ansible playbooks and configurations
- docker: Manage Docker configurations and files
- github_actions: Manage GitHub Actions workflows
- gitlab_ci: Manage GitLab CI/CD pipelines
- kestra: Manage Kestra workflows and configurations
- kubernetes: Manage Kubernetes manifests and configurations
- packer: Manage Packer templates and configurations
- terraform: Manage Terraform configurations and modules
- vagrant: Manage Vagrant configurations and files

Example:
    # In cli/modules/mymodule.py
    from ..core.module import Module
    
    class MyModule(Module):
        def __init__(self):
            super().__init__(
                name="mymodule",
                description="My module description",
                files=["config.yml", "settings.json"],
                vars={"key": "value"}  # optional
            )
        
        def register(self, app):
            return super().register(app)
"""