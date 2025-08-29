"""
Modules package for the Boilerplates CLI.
Contains all module implementations for different infrastructure types.
"""

from typing import List
from .ansible import AnsibleModule
from .docker import DockerModule
from .compose import ComposeModule
from .github_actions import GitHubActionsModule
from .gitlab_ci import GitLabCIModule
from .kestra import KestraModule
from .kubernetes import KubernetesModule
from .packer import PackerModule
from .terraform import TerraformModule
from .vagrant import VagrantModule

from ..core.command import BaseModule


def get_all_modules() -> List[BaseModule]:
    """
    Get all available CLI modules.
    
    Returns:
        List of initialized module instances.
    """
    return [
        AnsibleModule(),
        DockerModule(),
        ComposeModule(),
        GitHubActionsModule(),
        GitLabCIModule(),
        KestraModule(),
        KubernetesModule(),
        PackerModule(),
        TerraformModule(),
        VagrantModule(),
    ]
