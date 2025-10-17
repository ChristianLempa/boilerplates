# Compose Module - Variables Reference

**Schema Version:** `1.1`

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
| `network_mode` | enum (`bridge`, `host`, `macvlan`) | `bridge` | - | Docker network mode<br>*bridge=default Docker networking, host=use host network stack, macvlan=dedicated MAC address on physical network* |
| `network_name` | `str` | `bridge` | `network_mode=bridge,macvlan` | Docker network name |
| `network_external` | `bool` | `true` | `network_mode=bridge,macvlan` | Use existing Docker network |
| `network_macvlan_ipv4_address` | `str` | `192.168.1.253` | `network_mode=macvlan` | Static IP address for container |
| `network_macvlan_parent_interface` | `str` | `eth0` | `network_mode=macvlan` | Host network interface name |
| `network_macvlan_subnet` | `str` | `192.168.1.0/24` | `network_mode=macvlan` | Network subnet in CIDR notation |
| `network_macvlan_gateway` | `str` | `192.168.1.1` | `network_mode=macvlan` | Network gateway IP address |

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
**Depends on:** `traefik_enabled=true`

| Variable | Type | Default | Dependencies | Description |
|----------|------|---------|--------------|-------------|
| `traefik_tls_enabled` | `bool` | `true` | - | Enable HTTPS/TLS |
| `traefik_tls_entrypoint` | `str` | `websecure` | - | TLS entrypoint |
| `traefik_tls_certresolver` | `str` | `cloudflare` | - | Traefik certificate resolver name |

### Docker Swarm

Deploy service in Docker Swarm mode.


**Toggle:** `swarm_enabled` (default: `false`)

| Variable | Type | Default | Dependencies | Description |
|----------|------|---------|--------------|-------------|
| `swarm_enabled` | `bool` | `false` | - | Enable Docker Swarm mode |
| `swarm_placement_mode` | enum (`replicated`, `global`) | `replicated` | - | Swarm placement mode<br>*replicated=run specific number of tasks, global=run one task per node* |
| `swarm_replicas` | `int` | `1` | `swarm_placement_mode=replicated` | Number of replicas |
| `swarm_placement_host` | `str` | - | `swarm_placement_mode=replicated` | Target hostname for placement constraint<br>*Constrains service to run on specific node by hostname (optional)* |
| `swarm_volume_mode` | enum (`local`, `mount`, `nfs`) | `local` | - | Swarm volume storage backend<br>*WARNING: 'local' only works on single-node deployments!* |
| `swarm_volume_mount_path` | `str` | `/mnt/storage` | `swarm_volume_mode=mount` | Host path for bind mount<br>*Useful for shared/replicated storage* |
| `swarm_volume_nfs_server` | `str` | `192.168.1.1` | `swarm_volume_mode=nfs` | NFS server address<br>*IP address or hostname of NFS server* |
| `swarm_volume_nfs_path` | `str` | `/export` | `swarm_volume_mode=nfs` | NFS export path<br>*Path to NFS export on the server* |
| `swarm_volume_nfs_options` | `str` | `rw,nolock,soft` | `swarm_volume_mode=nfs` | NFS mount options<br>*Comma-separated NFS mount options* |

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
