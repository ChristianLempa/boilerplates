# Helm Variables

**Module:** `helm`  
**Schema Version:** `1.0`  
**Description:** Manage Helm charts

---

This page documents all available variables for the helm module. Variables are organized into sections that can be enabled/disabled based on your configuration needs.

## Table of Contents

- [General](#general)
- [Networking](#networking)
- [Traefik Ingress](#traefik-ingress)
- [Traefik TLS/SSL](#traefik-tlsssl)
- [Volumes](#volumes)
- [Database](#database)
- [Email Server](#email-server)

---

## General

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `release_name` | `str` | _none_ | Helm release name |
| `namespace` | `str` | `default` | Kubernetes namespace for the Helm release |

---

## Networking

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `network_mode` | `enum` | `ClusterIP` | Kubernetes service type<br>**Options:** `ClusterIP`, `NodePort`, `LoadBalancer` |

---

## Traefik Ingress

**Toggle Variable:** `traefik_enabled`  
**Depends On:** `network_mode=ClusterIP`

Traefik routes external traffic to your service.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `traefik_enabled` | `bool` | ✗ | Enable Traefik Ingress/IngressRoute |
| `traefik_host` | `hostname` | _none_ | Hostname for Traefik ingress |

---

## Traefik TLS/SSL

**Toggle Variable:** `traefik_tls_enabled`  
**Depends On:** `traefik_enabled=true;network_mode=ClusterIP`

Enable HTTPS/TLS for Traefik with certificate management.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `traefik_tls_enabled` | `bool` | ✓ | Enable HTTPS/TLS |
| `traefik_tls_secret` | `str` | `traefik-tls` | TLS secret name |
| `traefik_tls_certmanager` | `bool` | ✗ | Use cert-manager for automatic certificate provisioning |
| `certmanager_issuer` | `str` | `cloudflare` | Cert-manager ClusterIssuer or Issuer name<br>**Needs:** `traefik_tls_certmanager=true` |
| `certmanager_issuer_kind` | `enum` | `ClusterIssuer` | Issuer kind<br>**Options:** `ClusterIssuer`, `Issuer` • **Needs:** `traefik_tls_certmanager=true` |

---

## Volumes

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `volumes_mode` | `enum` | `default` | Persistent volume mode<br>**Options:** `default`, `existing-pvc` |
| `volumes_pvc_name` | `str` | _none_ | Name of existing PVC<br>**Needs:** `volumes_mode=existing-pvc` |

---

## Database

**Toggle Variable:** `database_enabled`

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `database_enabled` | `bool` | ✗ | Enable database configuration |
| `database_type` | `enum` | `postgres` | Database type<br>**Options:** `postgres`, `mysql`, `mariadb` |
| `database_host` | `hostname` | _none_ | Database host |
| `database_port` | `int` | _none_ | Database port |
| `database_name` | `str` | _none_ | Database name |
| `database_user` | `str` | _none_ | Database user |
| `database_password` | `str` | _none_ | Database password<br>**Sensitive** • **Auto-generated** |

---

## Email Server

**Toggle Variable:** `email_enabled`

Configure email server for notifications and user management.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `email_enabled` | `bool` | ✗ | Enable email server configuration |
| `email_host` | `hostname` | _none_ | SMTP server hostname |
| `email_port` | `int` | `587` | SMTP server port |
| `email_username` | `str` | _none_ | SMTP username |
| `email_password` | `str` | _none_ | SMTP password<br>**Sensitive** |
| `email_from` | `email` | _none_ | From email address |
| `email_use_tls` | `bool` | ✓ | Use TLS encryption |
| `email_use_ssl` | `bool` | ✗ | Use SSL encryption |

---

## Notes

- **Required sections** must be configured
- **Toggle variables** enable/disable entire sections
- **Dependencies** (`needs`) control when sections/variables are available
- **Sensitive variables** are masked during prompts
- **Auto-generated variables** are populated automatically if not provided

---

_Last updated: Schema version 1.0_