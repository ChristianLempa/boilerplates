"""Kubernetes module schema version 1.0 - Original specification."""

from collections import OrderedDict

spec = OrderedDict(
    {
        "general": {
            "title": "General",
            "vars": {
                "resource_name": {
                    "description": "Resource name (metadata.name)",
                    "type": "str",
                },
                "namespace": {
                    "description": "Kubernetes namespace",
                    "type": "str",
                    "default": "default",
                },
            },
        },
        "traefik": {
            "title": "Traefik",
            "toggle": "traefik_enabled",
            "description": "Traefik IngressRoute configuration for HTTP/HTTPS routing",
            "vars": {
                "traefik_enabled": {
                    "description": "Enable Traefik IngressRoute",
                    "type": "bool",
                    "default": False,
                },
                "traefik_entrypoint": {
                    "description": "Traefik entrypoint (non-TLS)",
                    "type": "str",
                    "default": "web",
                },
                "traefik_host": {
                    "description": "Domain name for the service (e.g., app.example.com)",
                    "type": "hostname",
                },
                "traefik_service_name": {
                    "description": "Backend Kubernetes service name",
                    "type": "str",
                },
                "traefik_service_port": {
                    "description": "Backend service port",
                    "type": "int",
                    "default": 80,
                },
            },
        },
        "traefik_tls": {
            "title": "Traefik TLS/SSL",
            "toggle": "traefik_tls_enabled",
            "needs": "traefik",
            "description": "Enable HTTPS/TLS for Traefik with certificate management",
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
        "certmanager": {
            "title": "Cert-Manager",
            "toggle": "certmanager_enabled",
            "description": "Cert-manager certificate management configuration",
            "vars": {
                "certmanager_enabled": {
                    "description": "Enable cert-manager certificate",
                    "type": "bool",
                    "default": False,
                },
                "certmanager_issuer": {
                    "description": "ClusterIssuer or Issuer name",
                    "type": "str",
                    "default": "cloudflare",
                },
                "certmanager_issuer_kind": {
                    "description": "Issuer kind",
                    "type": "enum",
                    "options": ["ClusterIssuer", "Issuer"],
                    "default": "ClusterIssuer",
                },
            },
        },
    }
)
