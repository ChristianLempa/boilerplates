"""Helm module schema version 1.0 - Original specification."""

from collections import OrderedDict

spec = OrderedDict(
    {
        "general": {
            "title": "General",
            "vars": {
                "release_name": {
                    "description": "Helm release name",
                    "type": "str",
                },
                "namespace": {
                    "description": "Kubernetes namespace for the Helm release",
                    "type": "str",
                    "default": "default",
                },
            },
        },
        "networking": {
            "title": "Networking",
            "vars": {
                "network_mode": {
                    "description": "Kubernetes service type",
                    "type": "enum",
                    "options": ["ClusterIP", "NodePort", "LoadBalancer"],
                    "default": "ClusterIP",
                },
            },
        },
        "traefik": {
            "title": "Traefik Ingress",
            "toggle": "traefik_enabled",
            "needs": "network_mode=ClusterIP",
            "description": "Traefik routes external traffic to your service.",
            "vars": {
                "traefik_enabled": {
                    "description": "Enable Traefik Ingress/IngressRoute",
                    "type": "bool",
                    "default": False,
                },
                "traefik_host": {
                    "description": "Hostname for Traefik ingress",
                    "type": "hostname",
                },
            },
        },
        "traefik_tls": {
            "title": "Traefik TLS/SSL",
            "toggle": "traefik_tls_enabled",
            "needs": "traefik_enabled=true;network_mode=ClusterIP",
            "description": "Enable HTTPS/TLS for Traefik with certificate management.",
            "vars": {
                "traefik_tls_enabled": {
                    "description": "Enable HTTPS/TLS",
                    "type": "bool",
                    "default": True,
                },
                "traefik_tls_secret": {
                    "description": "TLS secret name",
                    "type": "str",
                    "default": "traefik-tls",
                },
                "traefik_tls_certmanager": {
                    "description": "Use cert-manager for automatic certificate provisioning",
                    "type": "bool",
                    "default": False,
                },
                "certmanager_issuer": {
                    "description": "Cert-manager ClusterIssuer or Issuer name",
                    "type": "str",
                    "default": "cloudflare",
                    "needs": "traefik_tls_certmanager=true",
                },
                "certmanager_issuer_kind": {
                    "description": "Issuer kind",
                    "type": "enum",
                    "options": ["ClusterIssuer", "Issuer"],
                    "default": "ClusterIssuer",
                    "needs": "traefik_tls_certmanager=true",
                },
            },
        },
        "volumes": {
            "title": "Volumes",
            "vars": {
                "volumes_mode": {
                    "description": "Persistent volume mode",
                    "type": "enum",
                    "options": ["default", "existing-pvc"],
                    "default": "default",
                },
                "volumes_pvc_name": {
                    "description": "Name of existing PVC",
                    "type": "str",
                    "needs": "volumes_mode=existing-pvc",
                },
            },
        },
        "database": {
            "title": "Database",
            "toggle": "database_enabled",
            "vars": {
                "database_enabled": {
                    "description": "Enable database configuration",
                    "type": "bool",
                    "default": False,
                },
                "database_type": {
                    "description": "Database type",
                    "type": "enum",
                    "options": ["postgres", "mysql", "mariadb"],
                    "default": "postgres",
                },
                "database_host": {
                    "description": "Database host",
                    "type": "hostname",
                },
                "database_port": {
                    "description": "Database port",
                    "type": "int",
                },
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
                    "type": "hostname",
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
                    "type": "email",
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
    }
)
