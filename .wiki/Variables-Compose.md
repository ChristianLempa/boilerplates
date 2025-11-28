# Compose Variables

**Module:** `compose`  
**Schema Version:** `1.2`  
**Description:** Manage Docker Compose configurations

---

This page documents all available variables for the compose module. Variables are organized into sections that can be enabled/disabled based on your configuration needs.

## Table of Contents

- [General](#general)
- [Network](#network)
- [Ports](#ports)
- [Traefik](#traefik)
- [Traefik TLS/SSL](#traefik-tlsssl)
- [Volume Storage](#volume-storage)
- [Resource Limits](#resource-limits)
- [Docker Swarm](#docker-swarm)
- [Database](#database)
- [Email Server](#email-server)
- [Authentik SSO](#authentik-sso)

---

## General

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `service_name` | `str` | _none_ | Service name |
| `container_name` | `str` | _none_ | Container name |
| `container_hostname` | `str` | _none_ | Container internal hostname |
| `container_timezone` | `str` | `UTC` | Container timezone (e.g., Europe/Berlin) |
| `user_uid` | `int` | `1000` | User UID for container process |
| `user_gid` | `int` | `1000` | User GID for container process |
| `container_loglevel` | `enum` | `info` | Container log level<br>**Options:** `debug`, `info`, `warn`, `error` |
| `restart_policy` | `enum` | `unless-stopped` | Container restart policy<br>**Options:** `unless-stopped`, `always`, `on-failure`, `no` |

---

## Network

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `network_mode` | `enum` | `bridge` | Docker network mode<br>**Options:** `bridge`, `host`, `macvlan` |
| `network_name` | `str` | `bridge` | Docker network name<br>**Needs:** `network_mode=bridge,macvlan` |
| `network_external` | `bool` | ✗ | Use existing Docker network (external)<br>**Needs:** `network_mode=bridge,macvlan` |
| `network_macvlan_ipv4_address` | `str` | `192.168.1.253` | Static IP address for container<br>**Needs:** `network_mode=macvlan` |
| `network_macvlan_parent_interface` | `str` | `eth0` | Host network interface name<br>**Needs:** `network_mode=macvlan` |
| `network_macvlan_subnet` | `str` | `192.168.1.0/24` | Network subnet in CIDR notation<br>**Needs:** `network_mode=macvlan` |
| `network_macvlan_gateway` | `str` | `192.168.1.1` | Network gateway IP address<br>**Needs:** `network_mode=macvlan` |

---

## Ports

**Toggle Variable:** `ports_enabled`  
**Depends On:** `network_mode=bridge`

Expose service ports to the host.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ports_http` | `int` | `8080` | HTTP port on host |
| `ports_https` | `int` | `8443` | HTTPS port on host |
| `ports_ssh` | `int` | `22` | SSH port on host |
| `ports_dns` | `int` | `53` | DNS port on host |
| `ports_dhcp` | `int` | `67` | DHCP port on host |
| `ports_smtp` | `int` | `25` | SMTP port on host |

---

## Traefik

**Toggle Variable:** `traefik_enabled`  
**Depends On:** `network_mode=bridge`

Traefik routes external traffic to your service.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `traefik_enabled` | `bool` | ✗ | Enable Traefik reverse proxy integration |
| `traefik_network` | `str` | `traefik` | Traefik network name |
| `traefik_host` | `str` | _none_ | Service subdomain or full hostname (e.g., 'app' or 'app.example.com') |
| `traefik_domain` | `str` | `home.arpa` | Base domain (e.g., example.com) |
| `traefik_entrypoint` | `str` | `web` | HTTP entrypoint (non-TLS) |

---

## Traefik TLS/SSL

**Toggle Variable:** `traefik_tls_enabled`  
**Depends On:** `traefik_enabled=true;network_mode=bridge`

Enable HTTPS/TLS for Traefik with certificate management.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `traefik_tls_enabled` | `bool` | ✓ | Enable HTTPS/TLS |
| `traefik_tls_entrypoint` | `str` | `websecure` | TLS entrypoint |
| `traefik_tls_certresolver` | `str` | `cloudflare` | Traefik certificate resolver name |

---

## Volume Storage

Configure persistent storage for your service.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `volume_mode` | `enum` | `local` | Volume storage backend<br>**Options:** `local`, `mount`, `nfs` • local: Docker-managed volumes | mount: Bind mount from host | nfs: Network filesystem |
| `volume_mount_path` | `str` | `/mnt/storage` | Host path for bind mounts<br>**Needs:** `volume_mode=mount` |
| `volume_nfs_server` | `str` | `192.168.1.1` | NFS server address<br>**Needs:** `volume_mode=nfs` |
| `volume_nfs_path` | `str` | `/export` | NFS export path<br>**Needs:** `volume_mode=nfs` |
| `volume_nfs_options` | `str` | `rw,nolock,soft` | NFS mount options (comma-separated)<br>**Needs:** `volume_mode=nfs` |

---

## Resource Limits

**Toggle Variable:** `resources_enabled`

Set CPU and memory limits for the service.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `resources_enabled` | `bool` | ✗ | Enable resource limits |
| `resources_cpu_limit` | `str` | `1.0` | Maximum CPU cores (e.g., 0.5, 1.0, 2.0) |
| `resources_cpu_reservation` | `str` | `0.25` | Reserved CPU cores<br>**Needs:** `swarm_enabled=true` |
| `resources_memory_limit` | `str` | `1G` | Maximum memory (e.g., 512M, 1G, 2G) |
| `resources_memory_reservation` | `str` | `512M` | Reserved memory<br>**Needs:** `swarm_enabled=true` |

---

## Docker Swarm

**Toggle Variable:** `swarm_enabled`  
**Depends On:** `network_mode=bridge`

Deploy service in Docker Swarm mode.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `swarm_enabled` | `bool` | ✗ | Enable Docker Swarm mode |
| `swarm_placement_mode` | `enum` | `replicated` | Swarm placement mode<br>**Options:** `replicated`, `global` |
| `swarm_replicas` | `int` | `1` | Number of replicas<br>**Needs:** `swarm_placement_mode=replicated` |
| `swarm_placement_host` | `str` | _none_ | Target hostname for placement constraint<br>**Needs:** `swarm_placement_mode=replicated` • Constrains service to run on specific node by hostname |

---

## Database

**Toggle Variable:** `database_enabled`

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `database_type` | `enum` | `default` | Database type<br>**Options:** `default`, `sqlite`, `postgres`, `mysql` |
| `database_external` | `bool` | ✗ | Use an external database server?<br>skips creation of internal database container |
| `database_host` | `str` | `database` | Database host |
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
| `email_host` | `str` | _none_ | SMTP server hostname |
| `email_port` | `int` | `587` | SMTP server port |
| `email_username` | `str` | _none_ | SMTP username |
| `email_password` | `str` | _none_ | SMTP password<br>**Sensitive** |
| `email_from` | `str` | _none_ | From email address |
| `email_use_tls` | `bool` | ✓ | Use TLS encryption |
| `email_use_ssl` | `bool` | ✗ | Use SSL encryption |

---

## Authentik SSO

**Toggle Variable:** `authentik_enabled`

Integrate with Authentik for Single Sign-On authentication.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `authentik_enabled` | `bool` | ✗ | Enable Authentik SSO integration |
| `authentik_url` | `str` | _none_ | Authentik base URL (e.g., https://auth.example.com) |
| `authentik_slug` | `str` | _none_ | Authentik application slug |
| `authentik_client_id` | `str` | _none_ | OAuth client ID from Authentik provider |
| `authentik_client_secret` | `str` | _none_ | OAuth client secret from Authentik provider<br>**Sensitive** |
| `authentik_traefik_middleware` | `str` | `authentik-middleware@file` | Traefik middleware name for Authentik authentication<br>**Needs:** `traefik_enabled=true` |

---

## Notes

- **Required sections** must be configured
- **Toggle variables** enable/disable entire sections
- **Dependencies** (`needs`) control when sections/variables are available
- **Sensitive variables** are masked during prompts
- **Auto-generated variables** are populated automatically if not provided

---

_Last updated: Schema version 1.2_