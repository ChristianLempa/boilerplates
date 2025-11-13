# Templates

Templates are the core building blocks of the Boilerplates CLI. This page explains what templates are, how they work, and how to use them effectively.

## What is a Template?

A template is a **directory-based configuration package** that contains:
- **Metadata** - Name, description, version, author information
- **Variable specifications** - Configurable parameters
- **Template files** - Jinja2 templates that generate your configuration
- **Static files** - Files copied as-is (optional)

When you generate a template, the CLI:
1. Prompts you for variable values (or uses defaults/CLI overrides)
2. Renders template files using Jinja2
3. Writes the generated files to your specified directory

## Template Structure

Every template is a directory containing at minimum a `template.yaml` file:

```
template-name/
├── template.yaml          # Template definition and metadata
├── docker-compose.yml.j2  # Jinja2 template files
├── .env.j2               # Environment configuration
└── README.md             # Static file (copied as-is)
```

### The template.yaml File

This file defines everything about your template:

```yaml
---
kind: compose              # Module type (compose, terraform, ansible, etc.)
schema: "X.Y"             # Schema version (affects available features)
metadata:
  name: My Service
  description: Service description with Markdown support
  version: 1.0.0          # Application/service version
  author: Your Name
  date: '2025-01-12'
  tags:
    - docker
    - service
spec:
  # Variable specifications (see Variables page)
```

## Template Discovery

Templates are organized in **libraries**. A library is a collection of templates for a specific module type.

### Default Library Structure

```
~/.config/boilerplates/libraries/
└── default/
    └── library/
        ├── compose/
        │   ├── nginx/
        │   ├── traefik/
        │   └── whoami/
        ├── terraform/
        └── ansible/
```

### Finding Templates

```bash
# List all templates for a module
boilerplates compose list

# Search templates by name
boilerplates compose search proxy

# Show details about a template
boilerplates compose show nginx
```

## Template Metadata

### Required Fields

```yaml
metadata:
  name: Template Name        # Display name
  description: Description   # What the template does
  version: 1.0.0            # Application version
  author: Your Name         # Template author
  date: '2025-01-12'       # Last update date
```

### Optional Fields

```yaml
metadata:
  tags:                     # Searchable tags
    - docker
    - web-server
  draft: false             # Hide from listings if true
  next_steps: |            # Post-generation instructions
    ## What's Next
    1. Review the generated files
    2. Customize as needed
    3. Deploy!
```

### Description Markdown

The `description` field supports Markdown:

```yaml
metadata:
  description: |
    A **powerful reverse proxy** and load balancer.
    
    ## Features
    - Automatic HTTPS
    - Load balancing
    - Let's Encrypt integration
    
    ## Resources
    - **Project**: https://traefik.io
    - **Documentation**: https://doc.traefik.io
```

This renders nicely when you run `boilerplates compose show <template>`.

## Template Files

### Jinja2 Templates

Files ending in `.j2` are processed by Jinja2:

**docker-compose.yml.j2:**
```yaml
services:
  {{ service_name }}:
    image: nginx:{{ nginx_version }}
    ports:
      - "{{ nginx_port }}:80"
    {% if enable_ssl %}
    volumes:
      - ./ssl:/etc/nginx/ssl
    {% endif %}
```

After rendering with variables:
- `service_name=web`
- `nginx_version=1.25`
- `nginx_port=8080`
- `enable_ssl=true`

**Generated docker-compose.yml:**
```yaml
services:
  web:
    image: nginx:1.25
    ports:
      - "8080:80"
    volumes:
      - ./ssl:/etc/nginx/ssl
```

### Static Files

Files without `.j2` extension are copied as-is:
- `README.md` - Copied unchanged
- `scripts/setup.sh` - Copied unchanged

### File Includes

Templates can include other template files:

**main.j2:**
```jinja2
{% include 'common/header.j2' %}

services:
  {{ service_name }}:
    image: nginx:latest
```

**common/header.j2:**
```yaml
version: '3.8'
name: {{ project_name }}
```

## Schema Versioning

Templates declare a schema version that determines available features:

```yaml
schema: "X.Y"  # Use schema version X.Y (e.g., "1.0", "1.2")
```

**Why Schema Versions?**
- Modules evolve with new features over time
- Older templates continue working (backward compatibility)
- Templates opt-into new features by upgrading schema version

**Checking Current Schema:**

To find the latest schema version and available features for each module, refer to the module-specific variable documentation:
- [Compose Variables](Variables-Compose) - Shows current schema version at bottom
- [Terraform Variables](Variables-Terraform)
- [Ansible Variables](Variables-Ansible)
- [Kubernetes Variables](Variables-Kubernetes)
- [Helm Variables](Variables-Helm)
- [Packer Variables](Variables-Packer)

Each Variables page documents the current schema and which features are available.

## Template Lifecycle

### 1. Discovery

```bash
boilerplates repo update    # Sync libraries
boilerplates compose list   # Discover templates
```

### 2. Preview

```bash
boilerplates compose show nginx
```

Shows:
- Metadata
- Variable specifications
- File structure

### 3. Generation

```bash
# Interactive mode
boilerplates compose generate nginx

# Non-interactive mode
boilerplates compose generate nginx ./my-nginx \
  --var service_name=my-nginx \
  --no-interactive
```

### 4. Validation (Optional)

```bash
# Validate template structure
boilerplates compose validate nginx

# Validate all templates
boilerplates compose validate
```

## Template Identification

Templates are identified by their directory name:

```
library/compose/nginx/   → template ID: nginx
library/compose/traefik/ → template ID: traefik
```

### Qualified IDs

When using multiple libraries, templates can have qualified IDs:

```bash
# Simple ID (uses first matching template from priority order)
boilerplates compose generate nginx

# Qualified ID (targets specific library)
boilerplates compose generate nginx.local
boilerplates compose generate nginx.default
```

## Template Inheritance

Templates inherit variables from module specifications. You only need to override what's different.

**Module spec defines:**
- `service_name` (default: empty)
- `container_port` (default: 8080)
- `restart_policy` (default: unless-stopped)

**Template overrides:**
```yaml
spec:
  general:
    vars:
      service_name:
        default: nginx  # Override default
      # container_port inherits 8080
      # restart_policy inherits unless-stopped
```

This keeps templates concise—you only specify what's unique.

## Best Practices

### Naming Conventions

- **Template directories**: lowercase, hyphen-separated (`my-service`, `nginx-proxy`)
- **Service names**: match template name by default
- **File names**: descriptive and clear (`docker-compose.yml.j2`, not `dc.j2`)

### Version Management

**Application Versions:**
- Hardcode in template files: `image: nginx:1.25.3`
- Update `metadata.version` to match application
- Don't create version variables unless necessary

**Template Updates:**
- Increment `metadata.version` when updating
- Update `metadata.date` to current date
- Document changes in commit messages

### Documentation

- Use Markdown in `description`
- Provide `next_steps` for post-generation instructions
- Include links to official documentation
- Add usage examples

### Testing

Before publishing:
```bash
# Validate template
boilerplates compose validate my-template

# Test generation (dry run)
boilerplates compose generate my-template --dry-run

# Test with real generation
boilerplates compose generate my-template /tmp/test

# Verify generated files
cd /tmp/test && docker compose config
```

## Advanced Features

### Conditional File Generation

Use Jinja2 conditionals to skip entire sections:

```jinja2
{% if traefik_enabled %}
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.{{ service_name }}.rule=Host(`{{ traefik_host }}`)"
{% endif %}
```

### Dynamic File Names

Template file names can use variables (though this is rare):

```
config-{{ environment }}.yml.j2  # Generates: config-prod.yml
```

### Template Validation

Templates are validated on load:
- Jinja2 syntax errors detected
- Undefined variables reported
- Schema compatibility checked

## Next Steps

- [Variables](Core-Concepts-Variables) - Learn about variable types and configuration
- [Configuration](Core-Concepts-Libraries) - Manage template libraries
- [Variable Reference](Variables-Compose) - Complete variable documentation for modules
- [Developer Guide](Developers-Templates) - Create your own templates

## See Also

- [Getting Started](Getting-Started) - Generate your first template
- [Installation](Installation) - Install the CLI
