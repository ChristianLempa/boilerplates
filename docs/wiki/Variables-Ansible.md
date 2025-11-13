# Ansible Variables

**Module:** `ansible`  
**Schema Version:** `1.0`  
**Description:** Manage Ansible playbooks

---

This page documents all available variables for the ansible module. Variables are organized into sections that can be enabled/disabled based on your configuration needs.

## Table of Contents

- [General](#general)
- [Options](#options)
- [Secrets](#secrets)

---

## General

**Required:** Yes

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `playbook_name` | `str` | _none_ | Ansible playbook name |
| `target_hosts` | `str` | `{{ my_hosts | d([]) }}` | Target hosts pattern (e.g., 'all', 'webservers', or '{{ my_hosts | d([]) }}') |
| `become` | `bool` | ✗ | Run tasks with privilege escalation (sudo) |

---

## Options

**Toggle Variable:** `options_enabled`

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `options_enabled` | `bool` | ✗ | Enable additional playbook options |
| `gather_facts` | `bool` | ✓ | Gather facts about target hosts |

---

## Secrets

**Toggle Variable:** `secrets_enabled`

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `secrets_enabled` | `bool` | ✗ | Use external secrets file |
| `secrets_file` | `str` | `secrets.yaml` | Path to secrets file |

---

## Notes

- **Required sections** must be configured
- **Toggle variables** enable/disable entire sections
- **Dependencies** (`needs`) control when sections/variables are available
- **Sensitive variables** are masked during prompts
- **Auto-generated variables** are populated automatically if not provided

---

_Last updated: Schema version 1.0_