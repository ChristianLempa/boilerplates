# Christian's `Boilerplates` Library

This repository now contains only the infrastructure template library.

## Structure

All templates live under [library](library):

- [library/ansible](library/ansible)
- [library/compose](library/compose)
- [library/helm](library/helm)
- [library/kubernetes](library/kubernetes)
- [library/packer](library/packer)
- [library/terraform](library/terraform)

## Template Format

Each template directory uses JSON metadata:

- `template.json` for template metadata and variable contract
- `files/` for rendered source files

## Notes

- No CLI program is included in this repository.
- This is a library-only source repository for infrastructure templates.
