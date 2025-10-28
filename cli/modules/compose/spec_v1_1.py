"""Compose module schema version 1.1 - Enhanced with network_mode and improved swarm.

Changes from 1.0:
- network: Added network_mode (bridge/host/macvlan) with conditional macvlan fields
- swarm: Added volume modes (local/mount/nfs) and conditional placement constraints
- traefik_tls: Updated needs format from 'traefik' to 'traefik_enabled=true'
"""

from collections import OrderedDict

spec = OrderedDict(
    {
        "general": {
            "title": "General",
            "vars": {
                "service_name": {
                    "description": "Service name",
                    "type": "str",
                },
                "container_name": {
                    "description": "Container name",
                    "type": "str",
                },
                "container_hostname": {
                    "description": "Container internal hostname",
                    "type": "str",
                },
                "container_timezone": {
                    "description": "Container timezone (e.g., Europe/Berlin)",
                    "type": "str",
                    "default": "UTC",
                },
                "user_uid": {
                    "description": "User UID for container process",
                    "type": "int",
                    "default": 1000,
                },
                "user_gid": {
                    "description": "User GID for container process",
                    "type": "int",
                    "default": 1000,
                },
                "container_loglevel": {
                    "description": "Container log level",
                    "type": "enum",
                    "options": ["debug", "info", "warn", "error"],
                    "default": "info",
                },
                "restart_policy": {
                    "description": "Container restart policy",
                    "type": "enum",
                    "options": ["unless-stopped", "always", "on-failure", "no"],
                    "default": "unless-stopped",
                },
            },
        },
        "network": {
            "title": "Network",
            "vars": {
                "network_mode": {
                    "description": "Docker network mode",
                    "type": "enum",
                    "options": ["bridge", "host", "macvlan"],
                    "default": "bridge",
                },
                "network_name": {
                    "description": "Docker network name",
                    "type": "str",
                    "default": "bridge",
                    "needs": "network_mode=bridge,macvlan",
                },
                "network_external": {
                    "description": "Use existing Docker network (external)",
                    "type": "bool",
                    "default": False,
                    "needs": "network_mode=bridge,macvlan",
                },
                "network_macvlan_ipv4_address": {
                    "description": "Static IP address for container",
                    "type": "str",
                    "default": "192.168.1.253",
                    "needs": "network_mode=macvlan",
                },
                "network_macvlan_parent_interface": {
                    "description": "Host network interface name",
                    "type": "str",
                    "default": "eth0",
                    "needs": "network_mode=macvlan",
                },
                "network_macvlan_subnet": {
                    "description": "Network subnet in CIDR notation",
                    "type": "str",
                    "default": "192.168.1.0/24",
                    "needs": "network_mode=macvlan",
                },
                "network_macvlan_gateway": {
                    "description": "Network gateway IP address",
                    "type": "str",
                    "default": "192.168.1.1",
                    "needs": "network_mode=macvlan",
                },
            },
        },
        "ports": {
            "title": "Ports",
            "toggle": "ports_enabled",
            "needs": "network_mode=bridge",
            "vars": {
            },
        },
        "traefik": {
            "title": "Traefik",
            "toggle": "traefik_enabled",
            "needs": "network_mode=bridge",
            "description": "Traefik routes external traffic to your service.",
            "vars": {
                "traefik_enabled": {
                    "description": "Enable Traefik reverse proxy integration",
                    "type": "bool",
                    "default": False,
                },
                "traefik_network": {
                    "description": "Traefik network name",
                    "type": "str",
                    "default": "traefik",
                },
                "traefik_host": {
                    "description": "Domain name for your service (e.g., app.example.com)",
                    "type": "str",
                },
                "traefik_entrypoint": {
                    "description": "HTTP entrypoint (non-TLS)",
                    "type": "str",
                    "default": "web",
                },
            },
        },
        "traefik_tls": {
            "title": "Traefik TLS/SSL",
            "toggle": "traefik_tls_enabled",
            "needs": "traefik_enabled=true;network_mode=bridge",
            "description": "Enable HTTPS/TLS for Traefik with certificate management.",
            "vars": {
                "traefik_tls_enabled": {
                    "description": "Enable HTTPS/TLS",
                    "type": "bool",
                    "default": True,
                },
                "traefik_tls_entrypoint": {
                    "description": "TLS entrypoint",
                    "type": "str",
                    "default": "websecure",
                },
                "traefik_tls_certresolver": {
                    "description": "Traefik certificate resolver name",
                    "type": "str",
                    "default": "cloudflare",
                },
            },
        },
        "swarm": {
            "title": "Docker Swarm",
            "needs": "network_mode=bridge",
            "toggle": "swarm_enabled",
            "description": "Deploy service in Docker Swarm mode.",
            "vars": {
                "swarm_enabled": {
                    "description": "Enable Docker Swarm mode",
                    "type": "bool",
                    "default": False,
                },
                "swarm_placement_mode": {
                    "description": "Swarm placement mode",
                    "type": "enum",
                    "options": ["replicated", "global"],
                    "default": "replicated",
                },
                "swarm_replicas": {
                    "description": "Number of replicas",
                    "type": "int",
                    "default": 1,
                    "needs": "swarm_placement_mode=replicated",
                },
                "swarm_placement_host": {
                    "description": "Target hostname for placement constraint",
                    "type": "str",
                    "default": "",
                    "optional": True,
                    "needs": "swarm_placement_mode=replicated",
                    "extra": "Constrains service to run on specific node by hostname",
                },
                "swarm_volume_mode": {
                    "description": "Swarm volume storage backend",
                    "type": "enum",
                    "options": ["local", "mount", "nfs"],
                    "default": "local",
                    "extra": "WARNING: 'local' only works on single-node deployments!",
                },
                "swarm_volume_mount_path": {
                    "description": "Host path for bind mount",
                    "type": "str",
                    "default": "/mnt/storage",
                    "needs": "swarm_volume_mode=mount",
                    "extra": "Useful for shared/replicated storage",
                },
                "swarm_volume_nfs_server": {
                    "description": "NFS server address",
                    "type": "str",
                    "default": "192.168.1.1",
                    "needs": "swarm_volume_mode=nfs",
                    "extra": "IP address or hostname of NFS server",
                },
                "swarm_volume_nfs_path": {
                    "description": "NFS export path",
                    "type": "str",
                    "default": "/export",
                    "needs": "swarm_volume_mode=nfs",
                    "extra": "Path to NFS export on the server",
                },
                "swarm_volume_nfs_options": {
                    "description": "NFS mount options",
                    "type": "str",
                    "default": "rw,nolock,soft",
                    "needs": "swarm_volume_mode=nfs",
                    "extra": "Comma-separated NFS mount options",
                },
            },
        },
        "database": {
            "title": "Database",
            "toggle": "database_enabled",
            "vars": {
                "database_type": {
                    "description": "Database type",
                    "type": "enum",
                    "options": ["default", "sqlite", "postgres", "mysql"],
                    "default": "default",
                },
                "database_external": {
                    "description": "Use an external database server?",
                    "extra": "skips creation of internal database container",
                    "type": "bool",
                    "default": False,
                },
                "database_host": {
                    "description": "Database host",
                    "type": "str",
                    "default": "database",
                },
                "database_port": {"description": "Database port", "type": "int"},
                "database_name": {
                    "description": "Database name",
                    "type": "str",
                },
                "database_user": {
                    "description": "Database user",
                    "type": "str",
                },
                "database_password": {
                    "description": "Database password",
                    "type": "str",
                    "default": "",
                    "sensitive": True,
                    "autogenerated": True,
                },
            },
        },
        "email": {
            "title": "Email Server",
            "toggle": "email_enabled",
            "description": "Configure email server for notifications and user management.",
            "vars": {
                "email_enabled": {
                    "description": "Enable email server configuration",
                    "type": "bool",
                    "default": False,
                },
                "email_host": {
                    "description": "SMTP server hostname",
                    "type": "str",
                },
                "email_port": {
                    "description": "SMTP server port",
                    "type": "int",
                    "default": 587,
                },
                "email_username": {
                    "description": "SMTP username",
                    "type": "str",
                },
                "email_password": {
                    "description": "SMTP password",
                    "type": "str",
                    "sensitive": True,
                },
                "email_from": {
                    "description": "From email address",
                    "type": "str",
                },
                "email_use_tls": {
                    "description": "Use TLS encryption",
                    "type": "bool",
                    "default": True,
                },
                "email_use_ssl": {
                    "description": "Use SSL encryption",
                    "type": "bool",
                    "default": False,
                },
            },
        },
        "authentik": {
            "title": "Authentik SSO",
            "toggle": "authentik_enabled",
            "description": "Integrate with Authentik for Single Sign-On authentication.",
            "vars": {
                "authentik_enabled": {
                    "description": "Enable Authentik SSO integration",
                    "type": "bool",
                    "default": False,
                },
                "authentik_url": {
                    "description": "Authentik base URL (e.g., https://auth.example.com)",
                    "type": "str",
                },
                "authentik_slug": {
                    "description": "Authentik application slug",
                    "type": "str",
                },
                "authentik_client_id": {
                    "description": "OAuth client ID from Authentik provider",
                    "type": "str",
                },
                "authentik_client_secret": {
                    "description": "OAuth client secret from Authentik provider",
                    "type": "str",
                    "sensitive": True,
                },
            },
        },
    }
)
