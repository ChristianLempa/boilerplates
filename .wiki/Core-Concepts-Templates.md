# Templates

Templates are the core unit of Boilerplates. A supported template is a directory with a `template.json` manifest and a `files/` directory containing every renderable output file.

## Required Layout

```text
my-template/
├── template.json
└── files/
    ├── compose.yaml
    ├── .env
    └── config/
        └── app.yaml
```

Rules:
- `template.json` is the only supported manifest format
- all rendered content must live under `files/`
- legacy `template.yaml`, `template.yml`, and top-level `.j2` layouts are incompatible with the current runtime

## Top-Level Manifest Shape

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
    "author": "Your Name",
    "date": "2026-04-22",
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
      "notes": "Tracks the tested upstream dependency snapshot"
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

## `slug` and Template IDs

`slug` is the canonical template ID exposed by the CLI.

Behavior:
- if `slug` is present, it wins over the directory name
- if `slug` ends with `-<kind>`, that suffix is normalized away for CLI use
- if `slug` is missing, the directory name is used

Example:
- directory: `portainer/`
- `kind`: `compose`
- `slug`: `portainer-compose`
- CLI ID: `portainer`

## Metadata

Common metadata fields:
- `name`
- `description`
- `author`
- `date`
- `tags`
- `icon`
- `draft`
- `version`

### Version Metadata

`metadata.version` is optional, but when present it must be an object.

Supported fields:
- `name`
- `source_dep_name`
- `source_dep_version`
- `source_dep_digest`
- `upstream_ref`
- `notes`

Important behavior:
- `metadata.version.name` is the user-facing version label shown in list/show output
- the rest of the version object is for upstream dependency tracking
- the full object may be omitted
- individual fields inside the object may also be omitted

## Variable Declarations Are Mandatory

Any variable used in files under `files/` must be declared in `template.json`.

If a file references an undeclared variable, the template fails validation and load/render operations surface a template error.

Use the [Variables](Core-Concepts-Variables) page for the manifest structure.

## Files and Rendering

Everything under `files/` is part of the output tree.

Rendering behavior:
- Boilerplates walks every file under `files/`
- files are rendered with the custom delimiter set
- files without template expressions still pass through the render pipeline
- output paths currently mirror the relative paths inside `files/`
- rendered output is sanitized to normalize blank lines and trailing whitespace

## Delimiters

Templates use custom delimiters rather than default Jinja syntax:

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

Includes and imports resolve relative to the template's `files/` directory.

```jinja
<% include 'partials/header.yaml' %>
```

## Discovery Rules

Templates are discovered from configured libraries.

A directory is considered a valid template only when:
- `template.json` exists
- `files/` exists

In practice, Boilerplates discovers templates by module directory path such as `compose/<template>/` or `terraform/<template>/`.

Useful commands:

```bash
boilerplates compose list
boilerplates compose search nginx
boilerplates compose show nginx
```

Draft templates:
- set `metadata.draft` to `true` to hide the template from normal discovery

## Generation Workflow

Typical workflow:

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
- `--show-files` to print rendered files during dry-run

## Validation

Validate one template:

```bash
boilerplates compose validate nginx
```

Validate all templates in a module:

```bash
boilerplates compose validate
```

Validation covers:
- manifest structure
- variable declaration coverage
- delimiter compatibility
- renderability
- optional semantic validators for module-specific output

## Best Practices

- keep manifests in `template.json`
- keep every generated file under `files/`
- declare every variable that appears in rendered content
- use the custom delimiter set consistently
- hardcode tested upstream application versions in rendered files unless a variable is actually needed
- use `metadata.version.name` for the user-facing label
- use the remaining `metadata.version` fields for upstream snapshot context when useful
