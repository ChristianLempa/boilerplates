# Renovate Custom Managers

This document describes the custom regex managers configured for the boilerplates repository.

## 1. Docker Compose Templates

**File Pattern:** `library/compose/**/*.j2`

**Detects:** Docker images in compose files

**Example:**
```yaml
services:
  app:
    image: ghcr.io/goauthentik/server:2025.6.3
    # Renovate will detect: depName=ghcr.io/goauthentik/server, currentValue=2025.6.3
```

## 2. Kubernetes Helm Values

**File Patterns:** 
- `library/kubernetes/**/helm/values.yaml`
- `library/kubernetes/**/*.j2`

**Detects:** Docker images using repository + tag pattern (common in Helm charts)

**Example:**
```yaml
image:
  repository: "longhornio/longhorn-engine"
  tag: "v1.9.1"
# Renovate will detect: depName=longhornio/longhorn-engine, currentValue=v1.9.1
```

## 3. Terraform Providers

**File Patterns:**
- `library/terraform/**/*.tf`
- `library/terraform/**/*.j2`

**Detects:** Terraform provider versions

**Example:**
```hcl
terraform {
  required_providers {
    proxmox = {
      source  = "telmate/proxmox"
      version = "3.0.1-rc9"
    }
  }
}
# Renovate will detect: depName=telmate/proxmox, currentValue=3.0.1-rc9
```

## 4. Terraform Modules

**File Patterns:**
- `library/terraform/**/*.tf`
- `library/terraform/**/*.j2`

**Detects:** Terraform module versions from Git sources with `?ref=` parameter

**Example:**
```hcl
module "vpc" {
  source = "git::https://github.com/terraform-aws-modules/terraform-aws-vpc.git?ref=v5.1.2"
}
# Renovate will detect: depName=github.com/terraform-aws-modules/terraform-aws-vpc, currentValue=v5.1.2
```

## Post-Upgrade Tasks

After any dependency update, Renovate runs `.renovate/sync-template-version.sh` which:
1. Detects which `template.yaml` files were affected by the update
2. Automatically bumps their patch version
3. Includes the updated `template.yaml` files in the Renovate PR

This ensures template metadata stays in sync with dependency updates across all modules (compose, kubernetes, terraform).
