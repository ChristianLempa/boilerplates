# Libraries

Libraries are sources of templates. A library can be a Git repository or a local directory, and Boilerplates searches them in priority order.

## Default Library

By default, Boilerplates points to the official template library:

```text
Name: default
URL: https://github.com/christianlempa/boilerplates-library.git
Branch: main
Directory: .
```

## Supported Library Types

- `git`
- `static`

### Git Library Example

```yaml
libraries:
  - name: default
    type: git
    url: https://github.com/christianlempa/boilerplates-library.git
    branch: main
    directory: .
```

### Static Library Example

```yaml
libraries:
  - name: local
    type: static
    path: ~/my-templates
```

## Local Storage

Git libraries are stored under the active config directory's `libraries/` folder.

Global-config default:

```text
~/.config/boilerplates/libraries/
```

If the CLI is using a local `./config.yaml`, the library checkout location becomes `./libraries/`.

The configured `directory` is applied inside that checkout. For the official library the directory is `.`.

## Configuration Location

By default, Boilerplates uses:

```text
~/.config/boilerplates/config.yaml
```

If a local `./config.yaml` exists in your current working directory, the CLI uses that file instead.

## Discovery Rules

Boilerplates discovers templates by module directory, for example:

```text
compose/
terraform/
ansible/
```

A directory is treated as a template only when it contains `template.json`.

Legacy `template.yaml` and `template.yml` directories are ignored during discovery.

## Common Commands

List configured libraries:

```bash
boilerplates repo list
```

Sync Git libraries:

```bash
boilerplates repo update
```

Add a custom Git library:

```bash
boilerplates repo add my-templates \
  --library-type git \
  --url https://github.com/user/templates \
  --directory . \
  --branch main
```

Add a static library:

```bash
boilerplates repo add local \
  --library-type static \
  --path ~/my-templates
```

Remove a library:

```bash
boilerplates repo remove my-templates
```

## Priority and Qualified IDs

Libraries are checked in config order. The first matching template wins when you use a simple ID.

Example:

```yaml
libraries:
  - name: local
    type: static
    path: ~/my-templates
  - name: default
    type: git
    url: https://github.com/christianlempa/boilerplates-library.git
    branch: main
    directory: .
```

Simple ID:

```bash
boilerplates compose generate nginx
```

Qualified ID:

```bash
boilerplates compose generate nginx.local
boilerplates compose generate nginx.default
```

## Draft Templates

Templates with `metadata.draft: true` are excluded from normal listings and lookup.

## Config File

Example:

```yaml
libraries:
  - name: default
    type: git
    url: https://github.com/christianlempa/boilerplates-library.git
    branch: main
    directory: .
  - name: local
    type: static
    path: /Users/me/my-templates
```
