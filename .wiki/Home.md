# Boilerplates Wiki

Boilerplates is a CLI for discovering template libraries, inspecting template metadata and variables, and generating ready-to-use infrastructure files from `template.json` manifests.

The current runtime supports:
- `template.json` manifests only
- renderable files under `files/`
- custom delimiters: `<< >>`, `<% %>`, and `<# #>`
- structured optional `metadata.version` objects

## Start Here

- [Getting Started](Getting-Started) - install the CLI, sync a library, inspect a template, and generate files
- [Installation](Installation) - platform-specific installation options

## Core Concepts

- [Templates](Core-Concepts-Templates) - manifest shape, file layout, rendering rules, and version metadata
- [Variables](Core-Concepts-Variables) - variable groups, item fields, dependencies, toggles, and supported config
- [Libraries](Core-Concepts-Libraries) - official and custom libraries, discovery, priority, and config
- [Defaults](Core-Concepts-Defaults) - saved default values and precedence

## Variable Discovery

- [Variables](Variables) - how to inspect the variables a template actually exposes

## Additional Docs

- [Repository README](https://github.com/ChristianLempa/boilerplates/blob/main/README.md)
