# Renovate Configuration

This directory contains helper scripts and configuration for Renovate bot automation.

## Template Version Sync

### Overview

The `sync-template-version.sh` script automatically syncs Docker image versions from `compose.yaml.j2` files to their corresponding `template.yaml` metadata files.

### How It Works

1. **Renovate detects updates**: The custom regex manager in `renovate.json` detects Docker image versions in `.j2` template files
2. **Updates are applied**: When Renovate creates a PR, it updates the Docker image version in `compose.yaml.j2`
3. **Post-upgrade task runs**: After the update, the `sync-template-version.sh` script runs automatically
4. **Metadata synced**: The script extracts the first Docker image version from each `compose.yaml.j2` and updates the `version` field in the corresponding `template.yaml`

### Configuration

In `renovate.json`, the following configuration enables this feature:

```json
{
  "customManagers": [
    {
      "customType": "regex",
      "description": "Update Docker images in Jinja2 compose templates",
      "managerFilePatterns": [
        "/^library/compose/.+/compose\\.ya?ml\\.j2$/"
      ],
      "matchStrings": [
        "image:\\s*(?<depName>[^:\\s]+):(?<currentValue>[^\\s\\n{]+)"
      ],
      "datasourceTemplate": "docker"
    }
  ],
  "postUpgradeTasks": {
    "commands": [
      ".renovate/sync-template-version.sh"
    ],
    "fileFilters": [
      "library/compose/**/template.yaml"
    ],
    "executionMode": "update"
  }
}
```

### Manual Execution

You can run the script manually at any time:

```bash
./.renovate/sync-template-version.sh
```

This will scan all compose templates and update their metadata versions to match the Docker image versions.

### Limitations

- Only updates templates that have a Docker image with a version tag (e.g., `image: name:1.2.3`)
- Skips templates using Jinja2 variables for versions (e.g., `image: name:{{ version }}`)
- Uses the **first** image found in the `compose.yaml.j2` file (typically the main application image)
- Templates without `template.yaml` files are skipped

### Template Structure

Expected directory structure for each template:

```
library/compose/<template-name>/
├── compose.yaml.j2     # Jinja2 template with Docker Compose config
├── template.yaml       # Template metadata (includes version field)
└── ... (other files)
```

The `template.yaml` should have a `version` field in the metadata section:

```yaml
---
kind: compose
metadata:
  name: Application Name
  description: Description
  version: 0.1.0  # This will be auto-updated
  author: Christian Lempa
  date: '2025-10-02'
```

### Benefits

- **Consistency**: Template versions automatically track Docker image versions
- **Automation**: No manual version updates needed when Docker images are updated
- **Traceability**: Easy to see which Docker image version a template was designed for
