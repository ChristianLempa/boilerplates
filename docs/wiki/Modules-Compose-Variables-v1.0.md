# Compose Module - Variables Reference

**Schema Version:** `1.0`

This page documents all available variables for the module schema.
Variables are organized into sections, and some sections may be optional (toggled).

---

### General

**Required Section**

| Variable | Type | Default | Dependencies | Description |
|----------|------|---------|--------------|-------------|
| `service_name` | `str` | - | - | Service name |
| `container_name` | `str` | - | - | Container name |
| `container_hostname` | `str` | - | - | Container internal hostname |
| `container_timezone` | `str` | `UTC` | - | Container timezone (e.g., Europe/Berlin) |
| `user_uid` | `int` | `1000` | - | User UID for container process |
| `user_gid` | `int` | `1000` | - | User GID for container process |
| `container_loglevel` | enum (`debug`, `info`, `warn`, `error`) | `info` | - | Container log level |
| `restart_policy` | enum (`unless-stopped`, `always`, `on-failure`, `no`) | `unless-stopped` | - | Container restart policy |

### Network

**Toggle:** `network_enabled` (default: `false`)

| Variable | Type | Default | Dependencies | Description |
|----------|------|---------|--------------|-------------|
| `network_enabled` | `bool` | `false` | - | Enable custom network block |
| `network_name` | `str` | `bridge` | - | Docker network name |
| `network_external` | `bool` | `true` | - | Use existing Docker network |

### Ports

**Toggle:** `ports_enabled` (default: `true`)

| Variable | Type | Default | Dependencies | Description |
|----------|------|---------|--------------|-------------|
| `ports_enabled` | `bool` | `true` | - | Expose ports via 'ports' mapping |

### Traefik

Traefik routes external traffic to your service.


**Toggle:** `traefik_enabled` (default: `false`)

| Variable | Type | Default | Dependencies | Description |
|----------|------|---------|--------------|-------------|
| `traefik_enabled` | `bool` | `false` | - | Enable Traefik reverse proxy integration |
| `traefik_network` | `str` | `traefik` | - | Traefik network name |
| `traefik_host` | `str` | - | - | Domain name for your service (e.g., app.example.com) |
| `traefik_entrypoint` | `str` | `web` | - | HTTP entrypoint (non-TLS) |

### Traefik TLS/SSL

Enable HTTPS/TLS for Traefik with certificate management.


**Toggle:** `traefik_tls_enabled` (default: `true`)
**Depends on:** `traefik`

| Variable | Type | Default | Dependencies | Description |
|----------|------|---------|--------------|-------------|
| `traefik_tls_enabled` | `bool` | `true` | - | Enable HTTPS/TLS |
| `traefik_tls_entrypoint` | `str` | `websecure` | - | TLS entrypoint |
| `traefik_tls_certresolver` | `str` | `cloudflare` | - | Traefik certificate resolver name |

### Docker Swarm

Deploy service in Docker Swarm mode with replicas.


**Toggle:** `swarm_enabled` (default: `false`)

| Variable | Type | Default | Dependencies | Description |
|----------|------|---------|--------------|-------------|
| `swarm_enabled` | `bool` | `false` | - | Enable Docker Swarm mode |
| `swarm_replicas` | `int` | `1` | - | Number of replicas in Swarm |
| `swarm_placement_mode` | enum (`global`, `replicated`) | `replicated` | - | Swarm placement mode |
| `swarm_placement_host` | `str` | - | - | Limit placement to specific node |

### Database

Connect to external database (PostgreSQL or MySQL)


**Toggle:** `database_enabled` (default: `false`)

| Variable | Type | Default | Dependencies | Description |
|----------|------|---------|--------------|-------------|
| `database_enabled` | `bool` | `false` | - | Enable external database integration |
| `database_type` | enum (`postgres`, `mysql`) | `postgres` | - | Database type |
| `database_external` | `bool` | `false` | - | Use an external database server?<br>*If 'no', a database container will be created in the compose project.* |
| `database_host` | `str` | `database` | - | Database host |
| `database_port` | `int` | - | - | Database port |
| `database_name` | `str` | - | - | Database name |
| `database_user` | `str` | - | - | Database user |
| `database_password` | `str` | *auto-generated* | - | Database password 🔒 |

### Email Server

Configure email server for notifications and user management.


**Toggle:** `email_enabled` (default: `false`)

| Variable | Type | Default | Dependencies | Description |
|----------|------|---------|--------------|-------------|
| `email_enabled` | `bool` | `false` | - | Enable email server configuration |
| `email_host` | `str` | - | - | SMTP server hostname |
| `email_port` | `int` | `587` | - | SMTP server port |
| `email_username` | `str` | - | - | SMTP username |
| `email_password` | `str` | - | - | SMTP password 🔒 |
| `email_from` | `str` | - | - | From email address |
| `email_use_tls` | `bool` | `true` | - | Use TLS encryption |
| `email_use_ssl` | `bool` | `false` | - | Use SSL encryption |

### Authentik SSO

Integrate with Authentik for Single Sign-On authentication.


**Toggle:** `authentik_enabled` (default: `false`)

| Variable | Type | Default | Dependencies | Description |
|----------|------|---------|--------------|-------------|
| `authentik_enabled` | `bool` | `false` | - | Enable Authentik SSO integration |
| `authentik_url` | `str` | - | - | Authentik base URL (e.g., https://auth.example.com) |
| `authentik_slug` | `str` | - | - | Authentik application slug |
| `authentik_client_id` | `str` | - | - | OAuth client ID from Authentik provider |
| `authentik_client_secret` | `str` | - | - | OAuth client secret from Authentik provider 🔒 |

---

## Legend

- 🔒 = Sensitive variable (masked in prompts)
- *auto-generated* = Value automatically generated if not provided
- **Toggle** = Boolean variable that enables/disables the entire section
- **Depends on** = Section only active when dependencies are satisfied
