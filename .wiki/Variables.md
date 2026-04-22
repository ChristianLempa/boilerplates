# Variables Reference

Boilerplates no longer publishes static schema-version variable reference pages.

The current runtime is template-driven:
- modules provide baseline variable behavior
- each template can override defaults and add template-specific variables
- the exact variable set depends on the template you are inspecting

## How to Inspect Variables

Use the CLI against the template itself:

```bash
boilerplates compose show nginx
boilerplates terraform show cloudflare-dns-record
boilerplates ansible show ubuntu-vm-core
```

This shows:
- template metadata
- rendered version label from `metadata.version.name` when present
- the template file tree
- the actual variable groups and items exposed by that template

## Recommended Workflow

1. List templates for a module.
2. Show the template you want to use.
3. Review defaults, dependencies, and optional sections.
4. Generate with `--output`, `--var-file`, and `--var` as needed.

## Why the Old Pages Were Removed

The older wiki pages were generated from schema-version snapshots and no longer matched the current `template.json` runtime. They were removed to avoid documenting variables that may not exist, may have changed shape, or may be template-specific.
