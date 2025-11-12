#!/usr/bin/env python3
"""
Archetypes testing tool - for developing and testing template snippets.
Usage: python3 -m archetypes <module> <command>
"""

from __future__ import annotations

import builtins
import importlib
import logging
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

import click
import yaml

# Add parent directory to Python path for CLI imports
# This allows archetypes to import from cli module when run as `python3 -m archetypes`
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

# Import CLI components
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typer import Argument, Option, Typer

from cli.core.display import DisplayManager
from cli.core.exceptions import (
    TemplateRenderError,
)
from cli.core.module.helpers import parse_var_inputs
from cli.core.template.variable_collection import VariableCollection

app = Typer(
    help="Test and develop template snippets (archetypes) without full template structure.",
    add_completion=True,
    rich_markup_mode="rich",
)
console = Console()
display = DisplayManager()

# Base directory for archetypes
ARCHETYPES_DIR = Path(__file__).parent

# Similarity thresholds for archetype validation
SIMILARITY_EXACT = 0.95
SIMILARITY_HIGH = 0.7
SIMILARITY_PARTIAL = 0.3
COVERAGE_GOOD = 0.7
COVERAGE_FAIR = 0.4

# Display limits
MAX_DIFF_LINES = 10


def setup_logging(log_level: str = "WARNING") -> None:
    """Configure logging for debugging."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


class ArchetypeTemplate:
    """Simplified template for testing individual .j2 files."""

    def __init__(self, file_path: Path, module_name: str):
        self.file_path = file_path
        self.module_name = module_name
        self.id = file_path.stem  # Filename without extension
        self.template_dir = file_path.parent

        # Create a minimal template.yaml in memory
        self.metadata = type(
            "obj",
            (object,),
            {
                "name": f"Archetype: {self.id}",
                "description": f"Testing archetype from {file_path.name}",
                "version": "0.1.0",
                "author": "Testing",
                "library": "archetype",
                "tags": ["archetype", "test"],
            },
        )()

        # Parse spec from module if available
        self.variables = self._load_module_spec()

    def _load_module_spec(self) -> VariableCollection | None:
        """Load variable spec from module and merge with archetypes.yaml if present."""
        try:
            # Load archetype config to get schema version
            archetype_config = self._load_archetype_config()
            schema_version = archetype_config.get("schema", "1.0") if archetype_config else "1.0"

            # Import module spec with correct schema
            spec = self._import_module_spec(schema_version)
            if spec is None:
                return None

            spec_dict = self._convert_spec_to_dict(spec)
            if spec_dict is None:
                return None

            # Merge variables from archetypes.yaml
            if archetype_config and "vars" in archetype_config:
                self._merge_archetype_vars(spec_dict, archetype_config["vars"])

            return VariableCollection(spec_dict)
        except Exception as e:
            logging.warning(f"Could not load spec for module {self.module_name}: {e}")
            return None

    def _load_archetype_config(self) -> dict | None:
        """Load archetypes.yaml configuration file."""
        config_file = self.template_dir / "archetypes.yaml"
        if not config_file.exists():
            return None

        try:
            with config_file.open() as f:
                return yaml.safe_load(f)
        except Exception as e:
            logging.warning(f"Failed to load archetypes.yaml: {e}")
            return None

    def _import_module_spec(self, schema_version: str) -> Any | None:
        """Import module spec for the specified schema version."""
        module_path = f"cli.modules.{self.module_name}"
        try:
            module = importlib.import_module(module_path)

            # Try to get schema-specific spec if module supports it
            if hasattr(module, "SCHEMAS") and schema_version in module.SCHEMAS:
                spec = module.SCHEMAS[schema_version]
                logging.debug(f"Using schema {schema_version} for module {self.module_name}")
            else:
                # Fall back to default spec
                spec = getattr(module, "spec", None)

            if spec is None:
                logging.warning(f"Module {self.module_name} has no 'spec' attribute")
            return spec
        except (ImportError, AttributeError) as e:
            logging.warning(f"Could not load spec from {module_path}: {e}")
            return None

    def _convert_spec_to_dict(self, spec: Any) -> OrderedDict | None:
        """Convert spec to OrderedDict."""
        if isinstance(spec, (dict, OrderedDict)):
            return OrderedDict(spec)
        if isinstance(spec, VariableCollection):
            # Extract dict from existing VariableCollection (shouldn't happen)
            return OrderedDict()
        logging.warning(f"Spec for {self.module_name} has unexpected type: {type(spec)}")
        return None

    def _merge_archetype_vars(self, spec_dict: OrderedDict, archetype_vars: dict) -> None:
        """Merge variables from archetypes.yaml into spec_dict."""
        try:
            applied_count, new_vars = self._apply_archetype_vars(spec_dict, archetype_vars)
            self._add_testing_section(spec_dict, new_vars)

            logging.debug(f"Applied {applied_count} archetype var overrides, added {len(new_vars)} new test variables")
        except Exception as e:
            logging.warning(f"Failed to merge archetype vars: {e}")

    def _apply_archetype_vars(self, spec_dict: OrderedDict, archetype_vars: dict) -> tuple[int, dict]:
        """Apply archetype variables to existing spec sections or collect as new variables."""
        applied_count = 0
        new_vars = {}

        for var_name, var_spec in archetype_vars.items():
            if self._update_existing_var(spec_dict, var_name, var_spec):
                applied_count += 1
            else:
                new_vars[var_name] = var_spec

        return applied_count, new_vars

    def _update_existing_var(self, spec_dict: OrderedDict, var_name: str, var_spec: dict) -> bool:
        """Update existing variable with extension default."""
        if "default" not in var_spec:
            return False

        for _section_name, section_data in spec_dict.items():
            if "vars" in section_data and var_name in section_data["vars"]:
                section_data["vars"][var_name]["default"] = var_spec["default"]
                return True
        return False

    def _add_testing_section(self, spec_dict: OrderedDict, new_vars: dict) -> None:
        """Add new variables to testing section."""
        if not new_vars:
            return

        if "testing" not in spec_dict:
            spec_dict["testing"] = {
                "title": "Testing Variables",
                "description": "Additional variables for archetype testing",
                "vars": {},
            }
        spec_dict["testing"]["vars"].update(new_vars)

    def render(self, variables: dict[str, Any] | None = None) -> dict[str, str]:
        """Render the single .j2 file using CLI's Template class."""
        # Create a minimal template directory structure in memory
        # by using the Template class's rendering capabilities
        # Set up Jinja2 environment with the archetype directory
        env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Get variable values
        if variables is None:
            variables = {}

        # Get default values from spec if available
        if self.variables:
            # Get ALL variable values, not just satisfied ones
            # This is needed for archetype testing where we want full template context
            # Include None values so templates can properly handle optional variables
            spec_values = {}
            for _section_name, section in self.variables._sections.items():
                for var_name, var in section.variables.items():
                    # Include ALL variables, even if value is None
                    # This allows Jinja2 templates to handle optional variables properly
                    spec_values[var_name] = var.value
            # Merge: CLI variables override spec defaults
            final_values = {**spec_values, **variables}
        else:
            final_values = variables

        try:
            # Load and render the template
            template = env.get_template(self.file_path.name)
            rendered_content = template.render(**final_values)

            # Remove .j2 extension for output filename
            output_filename = self.file_path.name.replace(".j2", "")

            return {output_filename: rendered_content}
        except Exception as e:
            raise TemplateRenderError(f"Failed to render {self.file_path.name}: {e}") from e


def find_archetypes(module_name: str) -> list[Path]:
    """Find all .j2 files in the module's archetype directory.

    Excludes files matching the pattern '*-all-v*.j2' as these are
    typically composite archetypes used for testing/generation only.
    """
    module_dir = ARCHETYPES_DIR / module_name

    if not module_dir.exists():
        console.print(f"[red]Module directory not found: {module_dir}[/red]")
        return []

    # Find all .j2 files, excluding 'all-v*.j2' and '*-all-v*.j2' patterns
    j2_files = [f for f in module_dir.glob("*.j2") if not re.match(r"(.*-)?all-v.*\.j2$", f.name)]
    return sorted(j2_files)


def _find_archetype_by_id(archetypes: list[Path], id: str) -> Path | None:
    """Find an archetype file by its ID."""
    for path in archetypes:
        if path.stem == id:
            return path
    return None


def _create_list_table(module_name: str, archetypes: list[Path]) -> Table:
    """Create a table showing archetype files."""
    table = Table(
        title=f"Archetypes for '{module_name}'",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("ID", style="cyan")
    table.add_column("Filename", style="white")
    table.add_column("Size", style="dim")

    size_threshold = 1024
    for archetype_path in archetypes:
        file_size = archetype_path.stat().st_size
        size_str = f"{file_size}B" if file_size < size_threshold else f"{file_size / size_threshold:.1f}KB"
        table.add_row(archetype_path.stem, archetype_path.name, size_str)

    return table


def _display_archetype_details(archetype: ArchetypeTemplate, module_name: str) -> None:
    """Display archetype metadata and variables."""
    console.print()
    console.print(
        Panel(
            f"[bold]{archetype.metadata.name}[/bold]\n"
            f"{archetype.metadata.description}\n\n"
            f"[dim]Module:[/dim] {module_name}\n"
            f"[dim]File:[/dim] {archetype.file_path.name}\n"
            f"[dim]Path:[/dim] {archetype.file_path}",
            title="Archetype Details",
            border_style="cyan",
        )
    )

    if archetype.variables:
        console.print("\n[bold]Available Variables:[/bold]")
        for section_name, section in archetype.variables._sections.items():
            if section.variables:
                console.print(f"\n[cyan]{section.title or section_name.capitalize()}:[/cyan]")
                for var_name, var in section.variables.items():
                    default = var.value if var.value is not None else "[dim]none[/dim]"
                    console.print(f"  {var_name}: {default}")
    else:
        console.print("\n[yellow]No variable spec loaded for this module[/yellow]")


def _display_archetype_content(archetype_path: Path) -> None:
    """Display the archetype template file content."""
    console.print("\n[bold]Template Content:[/bold]")
    console.print("─" * 80)
    with archetype_path.open() as f:
        console.print(f.read())
    console.print()


def _parse_var_overrides(var: list[str] | None) -> dict[str, Any]:
    """Parse --var options into a dictionary with type conversion.

    Uses the CLI's parse_var_inputs function to ensure consistent behavior.
    """
    if not var:
        return {}

    # Use CLI's parse_var_inputs function (no extra_args for archetypes)
    return parse_var_inputs(var, [])


def _display_generated_preview(output_dir: Path, rendered_files: dict[str, str]) -> None:
    """Display the generated archetype preview."""
    console.print()
    console.print("[bold cyan]Archetype Preview (Testing Mode)[/bold cyan]")
    console.print("[dim]This tool never writes files - it's for testing template snippets only[/dim]")
    console.print(f"\n[dim]Reference directory:[/dim] {output_dir}\n")

    for filename, content in rendered_files.items():
        console.print(f"[bold cyan]{filename}[/bold cyan]")
        console.print("─" * 80)
        console.print(content)
        console.print()


def _normalize_template_content(content: str) -> list[str]:
    """Normalize template content for comparison.

    Removes blank lines, comments, and trims whitespace to focus on
    structural similarity rather than exact formatting.
    """
    lines = []
    for line in content.splitlines():
        stripped = line.strip()
        # Skip empty lines and comment-only lines
        if stripped and not stripped.startswith("#"):
            lines.append(stripped)
    return lines


def _extract_structural_pattern(content: str, is_archetype: bool = False) -> list[str]:  # noqa: PLR0912
    """Extract structural pattern from template content.

    Abstracts away specific values to focus on:
    - Jinja2 control structures (if/elif/else/endif/for/endfor)
    - YAML structure (keys, indentation levels)
    - Variable placeholders (replaced with generic <VAR>)
    - Literal values (replaced with generic <VALUE>)
    - Wildcard placeholders (__ANY__, __ANYSTR__, __ANYINT__, __ANYBOOL__)
    - Pattern markers (@repeat-start/end, @optional-start/end)

    Args:
        content: The template content to parse
        is_archetype: If True, preserves special markers and wildcards

    This allows comparing templates based on structure and logic
    rather than exact string matches.
    """
    lines = []
    for line in content.splitlines():
        # Skip empty lines
        stripped = line.strip()
        if not stripped:
            continue

        # Check for pattern markers (only in archetypes)
        if is_archetype and stripped.startswith("{#"):
            # Preserve pattern markers like @repeat-start, @optional-start, etc.
            if "@repeat-start" in stripped:
                lines.append("@REPEAT_START")
                continue
            if "@repeat-end" in stripped:
                lines.append("@REPEAT_END")
                continue
            if "@optional-start" in stripped:
                lines.append("@OPTIONAL_START")
                continue
            if "@optional-end" in stripped:
                lines.append("@OPTIONAL_END")
                continue
            if "@requires" in stripped:
                # Extract the requirement path (e.g., "services.*.configs")
                match = re.search(r"@requires\s+([^\s#}]+)", stripped)
                if match:
                    lines.append(f"@REQUIRES {match.group(1)}")
                continue
            # Skip other comments
            continue

        # Skip regular comments
        if stripped.startswith("#"):
            continue

        # Preserve indentation level (simplified to count of spaces)
        indent_level = len(line) - len(line.lstrip())
        indent_marker = "  " * (indent_level // 2)  # Normalize to 2-space indents

        # Keep Jinja2 control structures exactly as-is (no abstraction)
        if re.match(r"^{%\s*(if|elif|else|endif|for|endfor|block|endblock)\s*.*%}$", stripped):
            lines.append(indent_marker + stripped)
            continue

        # Keep Jinja2 variable interpolations as-is (preserve variable names)
        # We want to match exact variable usage, not abstract it
        normalized = stripped

        # Handle wildcard placeholders in archetypes
        if is_archetype:
            # Preserve wildcard patterns
            for wildcard in ["__ANY__", "__ANYSTR__", "__ANYINT__", "__ANYBOOL__"]:
                if wildcard in normalized:
                    # Keep wildcard as-is for archetype patterns
                    pass

        # Extract YAML key if present (key: value pattern)
        yaml_key_match = re.match(r"^-?\s*([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)$", normalized)
        if yaml_key_match:
            key = yaml_key_match.group(1)
            value = yaml_key_match.group(2)

            # Preserve key and value as-is (wildcards will be handled during matching)
            normalized_line = f"{key}: {value}" if value else f"{key}:"

            lines.append(indent_marker + normalized_line)
            continue

        # Handle list items (- value)
        if normalized.startswith("-"):
            # Preserve list values as-is
            lines.append(indent_marker + normalized)
            continue

        # Fallback: just preserve the abstracted line
        lines.append(indent_marker + normalized)

    return lines


def _pattern_matches_value(pattern: str, value: str) -> bool:
    """Check if a pattern (with wildcards) matches a value.

    Supports wildcards: __ANY__, __ANYSTR__, __ANYINT__, __ANYBOOL__, __ANYPATH__

    Args:
        pattern: The pattern string (may contain wildcards)
        value: The value to match against

    Returns:
        True if pattern matches value
    """
    # If no wildcards, must match exactly
    if "__ANY" not in pattern:
        return pattern == value

    # Build regex from pattern by replacing wildcards
    regex_pattern = re.escape(pattern)

    # Replace wildcards with appropriate regex patterns
    # Order matters: more specific before more general
    regex_pattern = regex_pattern.replace(r"__ANYPATH__", r"[^:]+")
    regex_pattern = regex_pattern.replace(r"__ANYINT__", r"\d+")
    regex_pattern = regex_pattern.replace(r"__ANYBOOL__", r"(?:true|false|yes|no)")
    regex_pattern = regex_pattern.replace(r"__ANYSTR__", r"[a-zA-Z0-9_-]+")
    regex_pattern = regex_pattern.replace(r"__ANY__", r".+")

    # Anchor the pattern
    regex_pattern = f"^{regex_pattern}$"

    return bool(re.match(regex_pattern, value, re.IGNORECASE))


def _normalize_pattern_line(line: str) -> str:
    """Normalize a pattern line by replacing wildcards with generic markers.

    Wildcards in archetypes get normalized to match any corresponding value.
    """
    # Replace wildcard patterns with match-any markers
    for wildcard in ["__ANY__", "__ANYSTR__", "__ANYINT__", "__ANYBOOL__"]:
        line = line.replace(wildcard, "<WILDCARD>")
    return line


def _extract_repeat_sections(pattern: list[str]) -> list[tuple[int, int, list[str]]]:
    """Extract repeat sections from a pattern.

    Returns:
        List of (start_idx, end_idx, section_content) tuples
    """
    sections = []
    i = 0
    while i < len(pattern):
        if pattern[i] == "@REPEAT_START":
            start = i + 1
            depth = 1
            j = i + 1
            while j < len(pattern) and depth > 0:
                if pattern[j] == "@REPEAT_START":
                    depth += 1
                elif pattern[j] == "@REPEAT_END":
                    depth -= 1
                j += 1
            end = j - 1
            sections.append((i, j, pattern[start:end]))
            i = j
        else:
            i += 1
    return sections


def _extract_optional_sections(pattern: list[str]) -> set[int]:
    """Extract indices of optional sections.

    Returns:
        Set of line indices that are within optional sections
    """
    optional_indices = set()
    i = 0
    while i < len(pattern):
        if pattern[i] == "@OPTIONAL_START":
            start = i + 1
            depth = 1
            j = i + 1
            while j < len(pattern) and depth > 0:
                if pattern[j] == "@OPTIONAL_START":
                    depth += 1
                elif pattern[j] == "@OPTIONAL_END":
                    depth -= 1
                j += 1
            end = j - 1
            # Mark all lines in this range as optional
            for idx in range(start, end):
                optional_indices.add(idx)
            i = j
        else:
            i += 1
    return optional_indices


def _check_requirement(requirement: str, template_pattern: list[str]) -> bool:
    """Check if a requirement path exists in the template.

    Args:
        requirement: Path like "services.*.configs" or "configs:"
        template_pattern: The template's structural pattern

    Returns:
        True if requirement is satisfied
    """
    # Parse requirement path
    parts = requirement.split(".")

    # Simple case: just check if key exists
    if len(parts) == 1:
        # Check for exact match or as YAML key
        search_term = parts[0].rstrip(":")
        return any(search_term in line for line in template_pattern)

    # Complex case: services.*.configs means "any service has configs"
    path_components = 3  # Expected: parent.*.child format
    if len(parts) == path_components and parts[1] == "*":
        # Look for the nested key within the parent section
        parent = parts[0]  # e.g., "services"
        child = parts[2]  # e.g., "configs"

        # Check if we can find parent section followed by child key
        in_parent = False
        for line in template_pattern:
            if parent in line and ":" in line:
                in_parent = True
            elif in_parent and child in line:
                return True
            # Reset if we hit another top-level key
            elif in_parent and line and not line.startswith((" ", "\t", "-")):
                in_parent = False

    return False


def _calculate_similarity(archetype_content: str, template_content: str, strict: bool = False) -> tuple[float, str]:  # noqa: PLR0911, PLR0912
    """Calculate similarity between archetype and template content.

    Uses structural pattern matching to compare templates based on:
    - Jinja2 control flow (if/elif/else/for)
    - YAML structure (keys and nesting)
    - Variable usage patterns (not specific values)
    - Wildcard matching (__ANY__, __ANYSTR__, etc.)
    - Repeat sections (@repeat-start/end)
    - Optional sections (@optional-start/end)

    This allows detection of archetypes even when specific names differ
    (e.g., grafana_data vs alloy_data).

    Args:
        archetype_content: The archetype template content
        template_content: The template to validate
        strict: If True, enforce that matches appear in order

    Returns:
        Tuple of (similarity_ratio, usage_status)
        - similarity_ratio: 0.0 to 1.0 (percentage of archetype structure found)
        - usage_status: "exact", "high", "partial", or "none"
    """
    archetype_pattern = _extract_structural_pattern(archetype_content, is_archetype=True)
    template_pattern = _extract_structural_pattern(template_content, is_archetype=False)

    if not archetype_pattern:
        return 0.0, "none"

    # Check for @requires marker - if requirement not met, return 0%
    for line in archetype_pattern:
        if line.startswith("@REQUIRES "):
            requirement = line.split(" ", 1)[1]
            if not _check_requirement(requirement, template_pattern):
                # Required section/key is missing from template
                return 0.0, "none"

    # Extract optional sections from RAW pattern
    raw_optional_indices = _extract_optional_sections(archetype_pattern)

    # Remove marker lines from archetype pattern for comparison
    # AND build a mapping from raw indices to cleaned indices
    cleaned_archetype = []
    raw_to_cleaned_map = {}
    cleaned_idx = 0

    for raw_idx, line in enumerate(archetype_pattern):
        excluded_markers = ("@REPEAT_START", "@REPEAT_END", "@OPTIONAL_START", "@OPTIONAL_END")
        if line not in excluded_markers and not line.startswith("@REQUIRES "):
            cleaned_archetype.append(line)
            raw_to_cleaned_map[raw_idx] = cleaned_idx
            cleaned_idx += 1

    # Map optional indices from raw to cleaned
    optional_indices = {raw_to_cleaned_map[i] for i in raw_optional_indices if i in raw_to_cleaned_map}

    if not cleaned_archetype:
        return 0.0, "none"

    # Count matches using wildcard-aware matching
    matched_lines = 0
    used_template_indices = set()
    matched_archetype_indices = set()
    last_matched_template_idx = -1  # Track last match position for strict mode

    for arch_idx, arch_line in enumerate(cleaned_archetype):
        # Try to find a matching line in template (that hasn't been matched yet)
        for i, temp_line in enumerate(template_pattern):
            if i in used_template_indices:
                continue

            # In strict mode, enforce ordering: matches must appear in increasing order
            if strict and i <= last_matched_template_idx:
                continue

            # Check if lines match (with wildcard support)
            if arch_line == temp_line or ("__ANY" in arch_line and _pattern_matches_value(arch_line, temp_line)):
                matched_lines += 1
                used_template_indices.add(i)
                matched_archetype_indices.add(arch_idx)
                last_matched_template_idx = i  # Update last match position
                break

    # Handle optional sections correctly:
    # - If optional section is NOT in template: exclude from denominator (don't penalize)
    # - If optional section IS in template: must fully comply (include in denominator)
    optional_lines_used = len([i for i in optional_indices if i in matched_archetype_indices])
    optional_lines_total = len(optional_indices)
    optional_lines_unused = optional_lines_total - optional_lines_used

    # Total = all lines - unused optional lines
    total_archetype_lines = len(cleaned_archetype) - optional_lines_unused

    # Ratio represents what percentage of the required archetype structure is found
    ratio = matched_lines / total_archetype_lines if total_archetype_lines > 0 else 0.0

    # Cap at 1.0 (100%) to prevent math errors
    ratio = min(ratio, 1.0)

    # Determine usage status based on structural match
    if ratio >= SIMILARITY_EXACT:
        return ratio, "exact"
    if ratio >= SIMILARITY_HIGH:
        return ratio, "high"
    if ratio >= SIMILARITY_PARTIAL:
        return ratio, "partial"
    return ratio, "none"


def _find_template_files(template_dir: Path) -> dict[str, Path]:
    """Find all template .j2 files in a template directory.

    Returns:
        Dict mapping template file stem (without .j2) to file path
    """
    template_files = {}
    if template_dir.exists():
        for j2_file in template_dir.glob("*.j2"):
            template_files[j2_file.stem] = j2_file
    return template_files


def _validate_template_against_archetypes(
    template_dir: Path,
    archetypes: list[Path],
    strict: bool = False,
) -> dict[str, dict[str, Any]]:
    """Validate a template directory against all archetypes.

    Args:
        template_dir: Directory containing the template
        archetypes: List of archetype file paths
        strict: If True, enforce ordering of elements

    Returns:
        Dict mapping archetype ID to validation results:
        {
            "archetype_id": {
                "ratio": 0.85,
                "status": "high",
                "template_file": Path(...) or None
            }
        }
    """
    template_files = _find_template_files(template_dir)
    results = {}

    for archetype_path in archetypes:
        archetype_id = archetype_path.stem

        # Load archetype content
        with archetype_path.open() as f:
            archetype_content = f.read()

        # Check if template has a matching file
        best_match = None
        best_ratio = 0.0
        best_status = "none"

        for _template_stem, template_path in template_files.items():
            with template_path.open() as f:
                template_content = f.read()

            ratio, status = _calculate_similarity(archetype_content, template_content, strict)

            if ratio > best_ratio:
                best_ratio = ratio
                best_status = status
                best_match = template_path

        results[archetype_id] = {"ratio": best_ratio, "status": best_status, "template_file": best_match}

    return results


def _get_pattern_diff(archetype_pattern: list[str], template_pattern: list[str]) -> tuple[list[str], list[str]]:
    """Get the differences between archetype and template patterns.

    Supports wildcard matching in archetype patterns.

    Returns:
        Tuple of (missing_lines, extra_lines)
        - missing_lines: Lines in archetype but not in template
        - extra_lines: Lines in template but not in archetype
    """
    matched_archetype_indices = set()
    matched_template_indices = set()

    # For each archetype line, check if it matches any template line
    for i, arch_line in enumerate(archetype_pattern):
        # Check for exact match first (fast path)
        if arch_line in template_pattern:
            matched_archetype_indices.add(i)
            # Mark the first matching template line
            template_idx = template_pattern.index(arch_line)
            matched_template_indices.add(template_idx)
            continue

        # Check for wildcard pattern match
        if "__ANY" in arch_line:
            for j, template_line in enumerate(template_pattern):
                if j in matched_template_indices:
                    continue
                if _pattern_matches_value(arch_line, template_line):
                    matched_archetype_indices.add(i)
                    matched_template_indices.add(j)
                    break

    missing_lines = [archetype_pattern[i] for i in range(len(archetype_pattern)) if i not in matched_archetype_indices]

    extra_lines = [template_pattern[i] for i in range(len(template_pattern)) if i not in matched_template_indices]

    return missing_lines, extra_lines


def _create_validation_table(template_id: str, validation_results: dict[str, dict[str, Any]]) -> Table:
    """Create a table showing archetype validation results."""
    table = Table(
        title=f"Archetype Validation: {template_id}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Archetype", style="cyan")
    table.add_column("Similarity", justify="right")
    table.add_column("Template File", style="dim")

    # Sort by similarity (highest first)
    sorted_results = sorted(validation_results.items(), key=lambda x: x[1]["ratio"], reverse=True)

    for archetype_id, result in sorted_results:
        ratio = result["ratio"]
        template_file = result["template_file"]

        # Color-code similarity based on thresholds
        if ratio >= SIMILARITY_EXACT or ratio >= SIMILARITY_HIGH:
            color = "green"
        elif ratio >= SIMILARITY_PARTIAL:
            color = "yellow"
        else:
            color = "red"

        ratio_text = f"[{color}]{ratio:.1%}[/{color}]"
        file_text = template_file.name if template_file else "--"

        table.add_row(archetype_id, ratio_text, file_text)

    return table


def _display_pattern_diff(archetype_id: str, archetype_path: Path, template_path: Path, ratio: float) -> None:
    """Display the structural differences between archetype and template."""
    # Load and extract patterns
    with archetype_path.open() as f:
        archetype_content = f.read()
    with template_path.open() as f:
        template_content = f.read()

    archetype_pattern = _extract_structural_pattern(archetype_content, is_archetype=True)
    template_pattern = _extract_structural_pattern(template_content, is_archetype=False)

    # Clean up markers from archetype pattern for diff display
    cleaned_archetype = [
        line
        for line in archetype_pattern
        if line not in ("@REPEAT_START", "@REPEAT_END", "@OPTIONAL_START", "@OPTIONAL_END")
        and not line.startswith("@REQUIRES ")
    ]

    missing_lines, extra_lines = _get_pattern_diff(cleaned_archetype, template_pattern)

    if not missing_lines and not extra_lines:
        console.print(f"\n[green]✓[/green] [bold]{archetype_id}[/bold]: Perfect match!")
        return

    console.print(f"\n[bold cyan]Differences for {archetype_id}[/bold cyan] ([dim]{ratio:.1%} match[/dim]):")

    if missing_lines:
        console.print("\n[yellow]  Missing from template:[/yellow]")
        for line in missing_lines[:MAX_DIFF_LINES]:
            console.print(f"    [red]-[/red] {line}")
        if len(missing_lines) > MAX_DIFF_LINES:
            console.print(f"    [dim]... and {len(missing_lines) - MAX_DIFF_LINES} more lines[/dim]")


def _calculate_overall_similarity(validation_results: dict[str, dict[str, Any]]) -> float:
    """Calculate overall similarity score, ignoring 0% matches.

    Args:
        validation_results: Dict mapping archetype ID to validation results

    Returns:
        Average similarity ratio (0.0 to 1.0), excluding 0% matches
    """
    non_zero_ratios = [result["ratio"] for result in validation_results.values() if result["ratio"] > 0]

    if not non_zero_ratios:
        return 0.0

    return sum(non_zero_ratios) / len(non_zero_ratios)


def _validate_all_templates(lib_dir: Path, archetypes: list[Path], module_name: str, strict: bool) -> None:
    """Validate all templates in a library against archetypes.

    Shows a summary table with overall similarity scores for each template.
    Ignores archetypes with 0% similarity when calculating overall score.
    """
    # Find all template directories
    template_dirs = [d for d in lib_dir.iterdir() if d.is_dir() and (d / "template.yaml").exists()]

    if not template_dirs:
        display.warning(
            "No templates found in library",
            context=f"directory: {lib_dir}",
        )
        return

    # Validate each template and collect results
    all_results = {}
    for template_dir in sorted(template_dirs):
        validation_results = _validate_template_against_archetypes(template_dir, archetypes, strict)
        overall_similarity = _calculate_overall_similarity(validation_results)
        all_results[template_dir.name] = {
            "overall_similarity": overall_similarity,
            "validation_results": validation_results,
        }

    # Create summary table
    table = Table(
        title=f"Archetype Validation Summary: {module_name}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Template", style="cyan")
    table.add_column("Overall Similarity", justify="right")
    table.add_column("Archetypes Used", justify="right")
    table.add_column("Total Archetypes", justify="right")

    # Sort by overall similarity (highest first)
    sorted_templates = sorted(all_results.items(), key=lambda x: x[1]["overall_similarity"], reverse=True)

    for template_name, result in sorted_templates:
        overall_sim = result["overall_similarity"]
        validation_results = result["validation_results"]

        # Count non-zero archetypes
        used_count = sum(1 for r in validation_results.values() if r["ratio"] > 0)
        total_count = len(validation_results)

        # Color-code based on similarity
        if overall_sim >= SIMILARITY_EXACT:
            color = "green"
        elif overall_sim >= SIMILARITY_HIGH:
            color = "yellow"
        elif overall_sim >= SIMILARITY_PARTIAL:
            color = "dim yellow"
        else:
            color = "red"

        sim_text = f"[{color}]{overall_sim:.1%}[/{color}]"
        table.add_row(template_name, sim_text, str(used_count), str(total_count))

    console.print()
    console.print(table)

    # Show overall statistics
    total_templates = len(all_results)
    if total_templates > 0:
        avg_similarity = sum(r["overall_similarity"] for r in all_results.values()) / total_templates
    else:
        avg_similarity = 0

    console.print()
    color = "green" if avg_similarity >= COVERAGE_GOOD else "yellow" if avg_similarity >= COVERAGE_FAIR else "red"
    console.print(
        f"[bold]Overall Statistics:[/bold] {total_templates} template(s) | "
        f"Average similarity: [{color}]{avg_similarity:.1%}[/]"
    )
    console.print("[dim]Note: Similarity scores exclude archetypes with 0% match[/dim]")


def create_module_commands(module_name: str) -> Typer:  # noqa: PLR0915
    """Create a Typer app with commands for a specific module."""
    module_app = Typer(help=f"Manage {module_name} archetypes")

    @module_app.command()
    def list() -> None:
        """List all archetype files for this module."""
        archetypes = find_archetypes(module_name)

        if not archetypes:
            display.warning(
                f"No archetypes found for module '{module_name}'",
                context=f"directory: {ARCHETYPES_DIR / module_name}",
            )
            return

        table = _create_list_table(module_name, archetypes)
        console.print(table)
        console.print(f"\n[dim]Found {len(archetypes)} archetype(s)[/dim]")

    @module_app.command()
    def show(
        id: str = Argument(..., help="Archetype ID (filename without .j2)"),
    ) -> None:
        """Show details of an archetype file."""
        archetypes = find_archetypes(module_name)
        archetype_path = _find_archetype_by_id(archetypes, id)

        if not archetype_path:
            display.error(f"Archetype '{id}' not found", context=f"module '{module_name}'")
            return

        _display_archetype_content(archetype_path)

    @module_app.command()
    def generate(
        id: str = Argument(..., help="Archetype ID (filename without .j2)"),
        directory: str | None = Argument(None, help="Output directory (for reference only - no files are written)"),
        var: builtins.list[str] | None = None,
    ) -> None:
        """Generate output from an archetype file (always in preview mode).

        Use --var/-v to set variables in KEY=VALUE format.
        """
        archetypes = find_archetypes(module_name)
        archetype_path = _find_archetype_by_id(archetypes, id)

        if not archetype_path:
            display.error(f"Archetype '{id}' not found", context=f"module '{module_name}'")
            return

        archetype = ArchetypeTemplate(archetype_path, module_name)
        variables = _parse_var_overrides(var)

        try:
            rendered_files = archetype.render(variables)
        except Exception as e:
            display.error(f"Failed to render archetype: {e}", context=f"archetype '{id}'")
            return

        output_dir = Path(directory) if directory else Path.cwd()
        _display_generated_preview(output_dir, rendered_files)
        display.success("Preview complete - no files were written")

    @module_app.command()
    def validate(
        template_id: str | None = Argument(
            None, help="Template ID or path to validate (omit to validate all templates)"
        ),
        library_path: str | None = Option(
            None, "--library", "-l", help="Path to template library (defaults to library/<module>)"
        ),
        show_diff: bool = Option(False, "--diff", "-d", help="Show detailed differences for non-exact matches"),
        strict: bool = Option(
            False, "--strict", help="Enforce ordering - elements must appear in same order as archetype"
        ),
    ) -> None:
        """Validate template(s) against archetypes to check usage coverage.

        Compares template files with archetype snippets and reports which
        archetype patterns are used and what differences exist.

        If no template_id is provided, validates ALL templates in the library
        and shows overall similarity scores (ignoring 0% matches).

        Use --strict to enforce that template elements appear in the same order
        as the archetype (for consistency checking).
        """
        archetypes = find_archetypes(module_name)

        if not archetypes:
            display.error(
                f"No archetypes found for module '{module_name}'", context=f"directory: {ARCHETYPES_DIR / module_name}"
            )
            return

        # Determine library path
        lib_dir = Path(library_path) if library_path else Path.cwd() / "library" / module_name

        if not lib_dir.exists():
            display.error(
                f"Library directory not found: {lib_dir}", context="Use --library to specify a different path"
            )
            return

        # If no template_id provided, validate ALL templates
        if template_id is None:
            _validate_all_templates(lib_dir, archetypes, module_name, strict)
            return

        # Single template validation (original behavior)
        # Find template to validate
        template_path = lib_dir / template_id
        if not template_path.exists():
            # Try as direct path
            template_path = Path(template_id)
            if not template_path.exists():
                display.error(f"Template not found: {template_id}", context=f"Searched in: {lib_dir}")
                return

        results = _validate_template_against_archetypes(
            template_path,
            archetypes,
            strict,
        )

        table = _create_validation_table(template_path.name, results)
        console.print()
        console.print(table)

        # Show summary stats
        counts = {"exact": 0, "high": 0, "partial": 0, "none": 0}
        for result in results.values():
            counts[result["status"]] += 1

        total = len(results)
        coverage = (counts["exact"] + counts["high"]) / total if total > 0 else 0

        console.print()
        color = "green" if coverage >= COVERAGE_GOOD else "yellow" if coverage >= COVERAGE_FAIR else "red"
        console.print(
            f"[bold]Summary:[/bold] {counts['exact']} exact, {counts['high']} high, "
            f"{counts['partial']} partial, {counts['none']} none | "
            f"Coverage: [{color}]{coverage:.1%}[/]"
        )

        # Show diffs if requested
        if show_diff:
            console.print("\n" + "=" * 80)
            console.print("[bold]Detailed Differences:[/bold]")
            console.print("=" * 80)

            # Show diffs for non-exact matches (sorted by ratio, highest first)
            sorted_results = sorted(results.items(), key=lambda x: x[1]["ratio"], reverse=True)

            for archetype_id, result in sorted_results:
                ratio = result["ratio"]

                # Skip perfect matches and archetypes with no template file
                if ratio >= SIMILARITY_EXACT or not result["template_file"]:
                    continue

                archetype_path = None
                for arch_path in archetypes:
                    if arch_path.stem == archetype_id:
                        archetype_path = arch_path
                        break

                if archetype_path:
                    _display_pattern_diff(archetype_id, archetype_path, result["template_file"], ratio)

    return module_app


def init_app() -> None:
    """Initialize the application by discovering modules and registering commands."""
    # Find all module directories in archetypes/
    if ARCHETYPES_DIR.exists():
        for module_dir in ARCHETYPES_DIR.iterdir():
            if module_dir.is_dir() and not module_dir.name.startswith(("_", ".")):
                module_name = module_dir.name
                # Register module commands
                module_app = create_module_commands(module_name)
                app.add_typer(module_app, name=module_name)


@app.callback(invoke_without_command=True)
def main(
    log_level: str | None = Option(
        None,
        "--log-level",
        help="Set logging level (DEBUG, INFO, WARNING, ERROR)",
    ),
) -> None:
    """Archetypes testing tool for template snippet development."""
    if log_level:
        setup_logging(log_level)
    else:
        logging.disable(logging.CRITICAL)

    ctx = click.get_current_context()

    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        sys.exit(0)


if __name__ == "__main__":
    try:
        init_app()
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
