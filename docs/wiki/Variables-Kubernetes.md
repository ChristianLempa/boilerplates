# Kubernetes Variables

**Module:** `kubernetes`  
**Schema Version:** `1.0`  
**Description:** Manage Kubernetes configurations

---

This page documents all available variables for the kubernetes module. Variables are organized into sections that can be enabled/disabled based on your configuration needs.

## Table of Contents

- [General](#general)
- [Traefik](#traefik)
- [Traefik TLS/SSL](#traefik-tlsssl)
- [Cert-Manager](#cert-manager)

---

## General

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `resource_name` | `str` | _none_ | Resource name (metadata.name) |
| `namespace` | `str` | `default` | Kubernetes namespace |

---

## Traefik

**Toggle Variable:** `traefik_enabled`

Traefik IngressRoute configuration for HTTP/HTTPS routing

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `traefik_enabled` | `bool` | ✗ | Enable Traefik IngressRoute |
| `traefik_entrypoint` | `str` | `web` | Traefik entrypoint (non-TLS) |
| `traefik_host` | `hostname` | _none_ | Domain name for the service (e.g., app.example.com) |
| `traefik_service_name` | `str` | _none_ | Backend Kubernetes service name |
| `traefik_service_port` | `int` | `80` | Backend service port |

---

## Traefik TLS/SSL

**Toggle Variable:** `traefik_tls_enabled`  
**Depends On:** `traefik`

Enable HTTPS/TLS for Traefik with certificate management

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `traefik_tls_enabled` | `bool` | ✓ | Enable HTTPS/TLS |
| `traefik_tls_entrypoint` | `str` | `websecure` | TLS entrypoint |
| `traefik_tls_certresolver` | `str` | `cloudflare` | Traefik certificate resolver name |

---

## Cert-Manager

**Toggle Variable:** `certmanager_enabled`

Cert-manager certificate management configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `certmanager_enabled` | `bool` | ✗ | Enable cert-manager certificate |
| `certmanager_issuer` | `str` | `cloudflare` | ClusterIssuer or Issuer name |
| `certmanager_issuer_kind` | `enum` | `ClusterIssuer` | Issuer kind<br>**Options:** `ClusterIssuer`, `Issuer` |

---

## Notes

- **Required sections** must be configured
- **Toggle variables** enable/disable entire sections
- **Dependencies** (`needs`) control when sections/variables are available
- **Sensitive variables** are masked during prompts
- **Auto-generated variables** are populated automatically if not provided

---

_Last updated: Schema version 1.0_