# Terraform Variables

**Module:** `terraform`  
**Schema Version:** `1.0`  
**Description:** Manage Terraform configurations

---

This page documents all available variables for the terraform module. Variables are organized into sections that can be enabled/disabled based on your configuration needs.

## Table of Contents

- [General](#general)

---

## General

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `resource_name` | `str` | _none_ | Resource name prefix |
| `backend_mode` | `enum` | `local` | Terraform backend mode<br>**Options:** `local`, `http` |

---

## Notes

- **Required sections** must be configured
- **Toggle variables** enable/disable entire sections
- **Dependencies** (`needs`) control when sections/variables are available
- **Sensitive variables** are masked during prompts
- **Auto-generated variables** are populated automatically if not provided

---

_Last updated: Schema version 1.0_