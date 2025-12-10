# Contributing to Boilerplates

Thank you for your interest in contributing to the Boilerplates project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [CLI Development](#cli-development)
- [Template Contributions](#template-contributions)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

Be respectful and constructive in all interactions. We're here to build great tools together.

## How to Contribute

### CLI Development

**IMPORTANT:** Any changes to the CLI application (`cli/` directory) require coordination.

**Before making CLI changes:**
1. Join the [Discord server](https://christianlempa.de/discord)
2. Reach out to discuss your proposed changes
3. Wait for approval before opening a PR

**Rationale:** The CLI architecture is complex and tightly integrated. Coordinating changes ensures consistency and prevents conflicts.

### Template Contributions

Template contributions are welcome and encouraged! You can:
- Add new templates to `library/`
- Improve existing templates
- Fix bugs in templates
- Update template documentation

**Process:**
1. Read the [Developer Documentation](../../wiki/Developers) in the Wiki
2. Create a new branch: `feature/###-template-name` or `problem/###-fix-description`
3. Add or modify templates following the structure in `library/`
4. Test your template thoroughly
5. Open a pull request

**No prior approval needed** for template contributions, but feel free to open an issue first to discuss larger changes.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- pipx (recommended) or pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ChristianLempa/boilerplates.git
cd boilerplates
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Run the CLI in development mode:
```bash
python3 -m cli --help
```

### Development Commands

```bash
# Run CLI with debug logging
python3 -m cli --log-level DEBUG compose list

# Test template generation
python3 -m cli compose generate template-name --dry-run

# Validate templates
python3 -m cli compose validate
```

## Code Standards

### Python Style Guide

- Follow PEP 8 conventions
- Use **2-space indentation** (project standard)
- Maximum line length: 100 characters
- Use type hints where appropriate

### Naming Conventions

- **Files:** lowercase with underscores (`variable_display.py`)
- **Classes:** PascalCase (`VariableCollection`, `DisplayManager`)
- **Functions/Methods:** snake_case (`render_template`, `get_spec`)
- **Constants:** UPPER_SNAKE_CASE (`DEFAULT_TIMEOUT`, `MAX_RETRIES`)
- **Private methods:** prefix with underscore (`_parse_section`)

### Comment Anchors

Use standardized comment anchors for important notes:

```python
# TODO: Implement feature X
# FIXME: Bug in validation logic
# NOTE: This is a workaround for issue #123
# LINK: https://docs.python.org/3/library/typing.html
```

### DisplayManager Usage

**CRITICAL RULE:**
- NEVER use `console.print()` outside of display manager classes
- NEVER import `Console` from `rich.console` except in display manager classes
- ALWAYS use `display.display_*()` methods for ALL output

```python
# GOOD
display = DisplayManager()
display.display_success("Template generated successfully")

# BAD
from rich.console import Console
console = Console()
console.print("Template generated")  # Don't do this!
```

### Docstrings

Use docstrings for all public classes and methods:

```python
def render_template(self, template: Template, template_id: str) -> None:
  """Render a complete template display.
  
  Args:
    template: The Template object to render
    template_id: The template identifier
  """
  pass
```

## Testing Guidelines

### Linting and Formatting

**REQUIRED before committing:**

```bash
# YAML files
yamllint library/

# Python code - check and auto-fix
ruff check --fix .

# Python code - format
ruff format .
```

### Validation Commands

```bash
# Validate all templates
python3 -m cli compose validate

# Validate specific template
python3 -m cli compose validate template-name

# Validate with semantic checks
python3 -m cli compose validate --semantic
```

### Manual Testing

Before submitting a PR, test your changes:

```bash
# Test template generation
python3 -m cli compose generate your-template --dry-run

# Test interactive mode
python3 -m cli compose generate your-template

# Test non-interactive mode
python3 -m cli compose generate your-template output-dir \
  --var service_name=test \
  --no-interactive
```

## Pull Request Process

### Branch Naming

- **Features:** `feature/###-description` (e.g., `feature/1234-add-nginx-template`)
- **Bug fixes:** `problem/###-description` (e.g., `problem/1235-fix-validation`)

### Commit Messages

Follow the format: `type(scope): subject`

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(compose): add nginx template
fix(display): correct variable rendering for enum types
docs(wiki): update installation instructions
refactor(template): simplify Jinja2 rendering logic
```

### PR Checklist

Before submitting a pull request:

- [ ] Code follows style guidelines (run `ruff check` and `ruff format`)
- [ ] YAML files pass `yamllint`
- [ ] All templates validate successfully
- [ ] Changes are tested manually
- [ ] Commit messages follow conventions
- [ ] PR description explains the changes
- [ ] Related issues are referenced (e.g., "Closes #1234")

### PR Review

- PRs require approval before merging
- Address review comments promptly
- Keep PRs focused and reasonably sized
- Squash commits if requested

## Issue Labels

When creating issues, use appropriate labels:

- `feature` - New feature requests
- `problem` - Bug reports
- `discussion` - General discussions
- `question` - Questions about usage
- `documentation` - Documentation improvements

## Getting Help

- Check the [Wiki](../../wiki) for documentation
- Join [Discord](https://christianlempa.de/discord) for discussions
- Open an issue for bugs or feature requests
- Watch [YouTube tutorials](https://www.youtube.com/@christianlempa)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to Boilerplates!
