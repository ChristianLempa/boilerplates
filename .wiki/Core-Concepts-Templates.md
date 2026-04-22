# Templates

Templates are the core unit of Boilerplates. A template is a directory with a `template.json` manifest and a `files/` directory containing the files to render.

## Template Structure

Every supported template looks like this:

```text
my-template/
├── template.json
└── files/
    ├── compose.yaml
    ├── .env
    └── config/
        └── app.yaml
```

Only `template.json` is a supported manifest format. Legacy `template.yaml` and `template.yml` manifests are not supported.

## Manifest Shape

Top-level fields:
- `slug`
- `kind`
- `metadata`
- `variables`

Example:

```json
{
  "slug": "my-template",
  "kind": "compose",
  "metadata": {
    "name": "My Template",
    "description": "Short human description",
    "tags": ["infra", "dev"],
    "icon": {
      "provider": "mdi",
      "id": "docker",
      "color": "blue"
    },
    "draft": false,
    "version": {
      "name": "v1.1",
      "source_dep_name": "ghcr.io/example/my-image",
      "source_dep_version": "1.1.0",
      "source_dep_digest": "sha256:abc123def456",
      "upstream_ref": "release-2026-04-22",
      "notes": "Tracks upstream container release used by this template snapshot"
    }
  },
  "variables": [
    {
      "name": "general",
      "title": "General",
      "items": [
        {
          "name": "service_name",
          "type": "str",
          "title": "Service name",
          "default": "my-service"
        }
      ]
    }
  ]
}
```

## Metadata

Common metadata fields:
- `name`
- `description`
- `tags`
- `icon`
- `draft`
- `author`
- `date`
- `guide`
- `version`

### Version Metadata

`metadata.version` is optional. If present, it must be an object.

Supported version fields:
- `name`
- `source_dep_name`
- `source_dep_version`
- `source_dep_digest`
- `upstream_ref`
- `notes`

Important rules:
- the whole `version` object may be omitted
- any individual `version` field may be omitted
- the CLI uses `metadata.version.name` as the visible version label in list/show output

This means these are all valid:

```json
{
  "metadata": {
    "name": "My Template"
  }
}
```

```json
{
  "metadata": {
    "name": "My Template",
    "version": {
      "name": "v1.1"
    }
  }
}
```

```json
{
  "metadata": {
    "name": "My Template",
    "version": {
      "source_dep_name": "ghcr.io/example/my-image",
      "source_dep_version": "1.1.0"
    }
  }
}
```

## Files and Rendering

All files inside `files/` are part of the template output.

Rendering rules:
- Boilerplates renders every file under `files/`
- files without template expressions pass through unchanged
- output paths currently match the relative file paths under `files/`
- template discovery ignores anything without `template.json`

## Delimiters

Templates use custom delimiters, not default Jinja syntax:

- variables: `<< value >>`
- blocks: `<% if condition %>`
- comments: `<# comment #>`

Example:

```yaml
services:
  << service_name >>:
    image: nginx:1.27.0
<% if ports_enabled %>
    ports:
      - "<< http_port >>:80"
<% endif %>
```

Legacy `{{ }}`, `{% %}`, and `{# #}` delimiters are rejected.

## Includes and Imports

Includes and imports are resolved relative to the template's `files/` directory.

Example:

```jinja
<% include 'partials/header.yaml' %>
```

## Template Discovery

Templates are discovered from configured libraries. A directory is considered a template only when it contains `template.json`.

Useful commands:

```bash
boilerplates compose list
boilerplates compose search nginx
boilerplates compose show nginx
```

Draft templates:
- set `metadata.draft` to `true` to hide a template from normal discovery

## Generation

Typical generation flow:

```bash
boilerplates compose show nginx
boilerplates compose generate nginx --output ./my-nginx
```

Useful flags:
- `--output` for local output
- `--remote` and `--remote-path` for SSH upload targets
- `--var-file` for YAML overrides
- `--var` for direct CLI overrides
- `--no-interactive` for non-interactive generation
- `--dry-run` to preview generation without writing files

## Validation

Validate one template:

```bash
boilerplates compose validate nginx
```

Validate all templates in a module:

```bash
boilerplates compose validate
```

## Best Practices

- keep manifests in `template.json`
- keep all generated content under `files/`
- use the custom delimiter set consistently
- hardcode tested upstream application versions in rendered files unless a variable is truly required
- use `metadata.version.name` for the user-facing label
- use the remaining `metadata.version` fields to track upstream dependency context when useful
