from __future__ import annotations

import base64
import logging
import os
import re
import secrets
import string
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml
from jinja2 import Environment, FileSystemLoader, meta
from jinja2.exceptions import (
    TemplateError as Jinja2TemplateError,
)
from jinja2.exceptions import (
    TemplateNotFound as Jinja2TemplateNotFound,
)
from jinja2.exceptions import (
    TemplateSyntaxError as Jinja2TemplateSyntaxError,
)
from jinja2.exceptions import (
    UndefinedError,
)
from jinja2.sandbox import SandboxedEnvironment

from ..exceptions import (
    RenderErrorContext,
    TemplateLoadError,
    TemplateRenderError,
    TemplateSyntaxError,
    TemplateValidationError,
    YAMLParseError,
)
from .variable_collection import VariableCollection

logger = logging.getLogger(__name__)

# Template Status Constants
TEMPLATE_STATUS_PUBLISHED = "published"
TEMPLATE_STATUS_DRAFT = "draft"
TEMPLATE_STATUS_INVALID = "invalid"


class TemplateErrorHandler:
    """Handles parsing and formatting of template rendering errors.

    This class provides utilities for:
    - Extracting error context from template files
    - Generating helpful suggestions based on Jinja2 errors
    - Parsing Jinja2 exceptions into structured error information
    """

    @staticmethod
    def extract_error_context(file_path: Path, line_number: int | None, context_size: int = 3) -> list[str]:
        """Extract lines of context around an error location.

        Args:
        file_path: Path to the file with the error
            line_number: Line number where error occurred (1-indexed)
            context_size: Number of lines to show before and after

        Returns:
            List of context lines with line numbers
        """
        if not line_number or not file_path.exists():
            return []

        try:
            with file_path.open(encoding="utf-8") as f:
                lines = f.readlines()

            start_line = max(0, line_number - context_size - 1)
            end_line = min(len(lines), line_number + context_size)

            context = []
            for i in range(start_line, end_line):
                line_num = i + 1
                marker = ">>>" if line_num == line_number else "   "
                context.append(f"{marker} {line_num:4d} | {lines[i].rstrip()}")

            return context
        except OSError:
            return []

    @staticmethod
    def get_common_jinja_suggestions(error_msg: str, available_vars: set) -> list[str]:
        """Generate helpful suggestions based on common Jinja2 errors.

        Args:
            error_msg: The error message from Jinja2
            available_vars: Set of available variable names

        Returns:
            List of actionable suggestions
        """
        suggestions = []
        error_lower = error_msg.lower()

        # Undefined variable errors
        if "undefined" in error_lower or "is not defined" in error_lower:
            # Try to extract variable name from error message
            var_match = re.search(r"'([^']+)'.*is undefined", error_msg)
            if not var_match:
                var_match = re.search(r"'([^']+)'.*is not defined", error_msg)

            if var_match:
                undefined_var = var_match.group(1)
                suggestions.append(f"Variable '{undefined_var}' is not defined in the template spec")

                # Suggest similar variable names (basic fuzzy matching)
                similar = [
                    v
                    for v in available_vars
                    if undefined_var.lower() in v.lower() or v.lower() in undefined_var.lower()
                ]
                if similar:
                    suggestions.append(f"Did you mean one of these? {', '.join(sorted(similar)[:5])}")

                suggestions.append(f"Add '{undefined_var}' to your template.yaml spec with a default value")
                suggestions.append("Or use the Jinja2 default filter: {{ " + undefined_var + " | default('value') }}")
            else:
                suggestions.append("Check that all variables used in templates are defined in template.yaml")
                suggestions.append("Use the Jinja2 default filter for optional variables: {{ var | default('value') }}")

        # Syntax errors
        elif "unexpected" in error_lower or "expected" in error_lower:
            suggestions.append("Check for syntax errors in your Jinja2 template")
            suggestions.append("Common issues: missing {% endfor %}, {% endif %}, or {% endblock %}")
            suggestions.append("Make sure all {{ }} and {% %} tags are properly closed")

        # Filter errors
        elif "filter" in error_lower:
            suggestions.append("Check that the filter name is spelled correctly")
            suggestions.append("Verify the filter exists in Jinja2 built-in filters")
            suggestions.append("Make sure filter arguments are properly formatted")

        # Template not found
        elif "not found" in error_lower or "does not exist" in error_lower:
            suggestions.append("Check that the included/imported template file exists")
            suggestions.append("Verify the template path is relative to the template directory")
            suggestions.append("Make sure the file has the .j2 extension if it's a Jinja2 template")

        # Type errors
        elif "type" in error_lower and ("int" in error_lower or "str" in error_lower or "bool" in error_lower):
            suggestions.append("Check that variable values have the correct type")
            suggestions.append("Use Jinja2 filters to convert types: {{ var | int }}, {{ var | string }}")

        # Add generic helpful tip
        if not suggestions:
            suggestions.append("Check the Jinja2 template syntax and variable usage")
            suggestions.append("Enable --debug mode for more detailed rendering information")

        return suggestions

    @classmethod
    def parse_jinja_error(
        cls,
        error: Exception,
        template_file: TemplateFile,
        template_dir: Path,
        available_vars: set,
    ) -> tuple[str, int | None, int | None, list[str], list[str]]:
        """Parse a Jinja2 exception to extract detailed error information.

        Args:
            error: The Jinja2 exception
            template_file: The TemplateFile being rendered
            template_dir: Template directory path
            available_vars: Set of available variable names

        Returns:
            Tuple of (error_message, line_number, column, context_lines, suggestions)
        """
        error_msg = str(error)
        line_number = None
        column = None
        context_lines = []
        suggestions = []

        # Extract line number from Jinja2 errors
        if hasattr(error, "lineno"):
            line_number = error.lineno

        # Extract file path and get context
        file_path = template_dir / template_file.relative_path
        if line_number and file_path.exists():
            context_lines = cls.extract_error_context(file_path, line_number)

        # Generate suggestions based on error type
        if isinstance(error, UndefinedError):
            error_msg = f"Undefined variable: {error}"
            suggestions = cls.get_common_jinja_suggestions(str(error), available_vars)
        elif isinstance(error, Jinja2TemplateSyntaxError):
            error_msg = f"Template syntax error: {error}"
            suggestions = cls.get_common_jinja_suggestions(str(error), available_vars)
        elif isinstance(error, Jinja2TemplateNotFound):
            error_msg = f"Template file not found: {error}"
            suggestions = cls.get_common_jinja_suggestions(str(error), available_vars)
        else:
            # Generic Jinja2 error
            suggestions = cls.get_common_jinja_suggestions(error_msg, available_vars)

        return error_msg, line_number, column, context_lines, suggestions


@dataclass
class TemplateFile:
    """Represents a single file within a template directory."""

    relative_path: Path
    file_type: Literal["j2", "static"]
    output_path: Path  # The path it will have in the output directory


@dataclass
class TemplateMetadata:
    """Represents template metadata with proper typing."""

    name: str
    description: str
    author: str
    date: str
    version: str
    module: str = ""
    tags: list[str] = field(default_factory=list)
    library: str = "unknown"
    library_type: str = "git"  # Type of library ("git" or "static")
    next_steps: str = ""
    draft: bool = False

    def __init__(
        self,
        template_data: dict,
        library_name: str | None = None,
        library_type: str = "git",
    ) -> None:
        """Initialize TemplateMetadata from parsed YAML template data.

        Args:
            template_data: Parsed YAML data from template.yaml
            library_name: Name of the library this template belongs to
        """
        # Validate metadata format first
        self._validate_metadata(template_data)

        # Extract metadata section
        metadata_section = template_data.get("metadata", {})

        self.name = metadata_section.get("name", "")
        # YAML block scalar (|) preserves a trailing newline. Remove only trailing newlines
        # while preserving internal newlines/formatting.
        raw_description = metadata_section.get("description", "")
        # TODO: remove when all templates have been migrated to markdown
        description = raw_description.rstrip("\n") if isinstance(raw_description, str) else str(raw_description)
        self.description = description or "No description available"
        self.author = metadata_section.get("author", "")
        self.date = metadata_section.get("date", "")
        self.version = metadata_section.get("version", "")
        self.module = metadata_section.get("module", "")
        self.tags = metadata_section.get("tags", []) or []
        self.library = library_name or "unknown"
        self.library_type = library_type
        self.draft = metadata_section.get("draft", False)

        # Extract next_steps (optional)
        raw_next_steps = metadata_section.get("next_steps", "")
        if isinstance(raw_next_steps, str):
            next_steps = raw_next_steps.rstrip("\n")
        else:
            next_steps = str(raw_next_steps) if raw_next_steps else ""
        self.next_steps = next_steps

    @staticmethod
    def _validate_metadata(template_data: dict) -> None:
        """Validate that template has required 'metadata' section with all required fields.

        Args:
            template_data: Parsed YAML data from template.yaml

        Raises:
            ValueError: If metadata section is missing or incomplete
        """
        metadata_section = template_data.get("metadata")
        if metadata_section is None:
            raise ValueError("Template format error: missing 'metadata' section")

        # Validate that metadata section has all required fields
        required_fields = ["name", "author", "version", "date", "description"]
        missing_fields = [field for field in required_fields if not metadata_section.get(field)]

        if missing_fields:
            raise ValueError(f"Template format error: missing required metadata fields: {missing_fields}")


@dataclass
class Template:
    """Represents a template directory."""

    def __init__(self, template_dir: Path, library_name: str, library_type: str = "git") -> None:
        """Create a Template instance from a directory path.

        Args:
            template_dir: Path to the template directory
            library_name: Name of the library this template belongs to
            library_type: Type of library ("git" or "static"), defaults to "git"
        """
        logger.debug(f"Loading template from directory: {template_dir}")
        self.template_dir = template_dir
        self.id = template_dir.name
        self.original_id = template_dir.name  # Store the original ID
        self.library_name = library_name
        self.library_type = library_type

        # Initialize caches for lazy loading
        self.__jinja_env: Environment | None = None
        self.__used_variables: set[str] | None = None
        self.__variables: VariableCollection | None = None
        self.__template_files: list[TemplateFile] | None = None  # New attribute

        try:
            # Find and parse the main template file (template.yaml or template.yml)
            main_template_path = self._find_main_template_file()
            with main_template_path.open(encoding="utf-8") as f:
                # Load all YAML documents (handles templates with empty lines before ---)
                documents = list(yaml.safe_load_all(f))

                # Filter out None/empty documents and get the first non-empty one
                valid_docs = [doc for doc in documents if doc is not None]

                if not valid_docs:
                    raise ValueError("Template file contains no valid YAML data")

                if len(valid_docs) > 1:
                    logger.warning("Template file contains multiple YAML documents, using the first one")

                self._template_data = valid_docs[0]

            # Validate template data
            if not isinstance(self._template_data, dict):
                raise ValueError("Template file must contain a valid YAML dictionary")

            # Load metadata (always needed)
            self.metadata = TemplateMetadata(self._template_data, library_name, library_type)
            logger.debug(f"Loaded metadata: {self.metadata}")

            # Validate 'kind' field (always needed)
            self._validate_kind(self._template_data)

            # NOTE: File collection is now lazy-loaded via the template_files property
            # This significantly improves performance when listing many templates

            logger.info(f"Loaded template '{self.id}' (v{self.metadata.version})")

        except (ValueError, FileNotFoundError) as e:
            logger.error(f"Error loading template from {template_dir}: {e}")
            raise TemplateLoadError(f"Error loading template from {template_dir}: {e}") from e
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in template {template_dir}: {e}")
            raise YAMLParseError(str(template_dir / "template.y*ml"), e) from e
        except OSError as e:
            logger.error(f"File I/O error loading template {template_dir}: {e}")
            raise TemplateLoadError(f"File I/O error loading template from {template_dir}: {e}") from e

    def set_qualified_id(self, library_name: str | None = None) -> None:
        """Set a qualified ID for this template (used when duplicates exist across libraries).

        Args:
            library_name: Name of the library to qualify with. If None, uses self.library_name
        """
        lib_name = library_name or self.library_name
        self.id = f"{self.original_id}.{lib_name}"
        logger.debug(f"Template ID qualified: {self.original_id} -> {self.id}")

    def _find_main_template_file(self) -> Path:
        """Find the main template file (template.yaml or template.yml)."""
        for filename in ["template.yaml", "template.yml"]:
            path = self.template_dir / filename
            if path.exists():
                return path
        raise FileNotFoundError(f"Main template file (template.yaml or template.yml) not found in {self.template_dir}")

    def _warn_about_unused_variables(self, template_specs: dict) -> None:
        """Warn about variables defined in spec but not used in template files.

        This helps identify unnecessary variable definitions that can be removed.

        Args:
            template_specs: Variables defined in template.yaml spec
        """
        # Collect variables explicitly defined in template
        defined_vars = set()
        for section_data in (template_specs or {}).values():
            if isinstance(section_data, dict) and "vars" in section_data:
                defined_vars.update(section_data["vars"].keys())

        # Get variables actually used in template files
        used_vars = self.used_variables

        # Find variables that are defined but not used
        unused_vars = defined_vars - used_vars

        if unused_vars:
            # Show first N variables in warning, full list in debug
            max_shown_vars = 10
            shown_vars = sorted(list(unused_vars)[:max_shown_vars])
            ellipsis = "..." if len(unused_vars) > max_shown_vars else ""
            logger.warning(
                f"Template '{self.id}' defines {len(unused_vars)} variable(s) that are not used in template files. "
                f"Consider removing them from the spec: {', '.join(shown_vars)}{ellipsis}"
            )
            logger.debug(f"Template '{self.id}' unused variables: {sorted(unused_vars)}")

    def _collect_template_files(self) -> None:
        """Collects all TemplateFile objects in the template directory."""
        template_files: list[TemplateFile] = []

        for root, _, files in os.walk(self.template_dir):
            for filename in files:
                file_path = Path(root) / filename
                relative_path = file_path.relative_to(self.template_dir)

                # Skip the main template file
                if filename in ["template.yaml", "template.yml"]:
                    continue

                if filename.endswith(".j2"):
                    file_type: Literal["j2", "static"] = "j2"
                    output_path = relative_path.with_suffix("")  # Remove .j2 suffix
                else:
                    file_type = "static"
                    output_path = relative_path  # Static files keep their name

                template_files.append(
                    TemplateFile(
                        relative_path=relative_path,
                        file_type=file_type,
                        output_path=output_path,
                    )
                )

        self.__template_files = template_files

    def _extract_all_used_variables(self) -> set[str]:
        """Extract all undeclared variables from all .j2 files in the template directory.

        Raises:
            ValueError: If any Jinja2 template has syntax errors
        """
        used_variables: set[str] = set()
        syntax_errors = []
        # Track which file uses which variable (for debugging)
        self._variable_usage_map: dict[str, list[str]] = {}

        for template_file in self.template_files:  # Iterate over TemplateFile objects
            if template_file.file_type == "j2":
                file_path = self.template_dir / template_file.relative_path
                try:
                    with file_path.open(encoding="utf-8") as f:
                        content = f.read()
                        ast = self.jinja_env.parse(content)  # Use lazy-loaded jinja_env
                        file_vars = meta.find_undeclared_variables(ast)
                        used_variables.update(file_vars)
                        # Track which file uses each variable
                        for var in file_vars:
                            if var not in self._variable_usage_map:
                                self._variable_usage_map[var] = []
                            self._variable_usage_map[var].append(str(template_file.relative_path))
                except OSError as e:
                    relative_path = file_path.relative_to(self.template_dir)
                    syntax_errors.append(f"  - {relative_path}: File I/O error: {e}")
                except Exception as e:
                    # Collect syntax errors for Jinja2 issues
                    relative_path = file_path.relative_to(self.template_dir)
                    syntax_errors.append(f"  - {relative_path}: {e}")

        # Raise error if any syntax errors were found
        if syntax_errors:
            logger.error(f"Jinja2 syntax errors found in template '{self.id}'")
            raise TemplateSyntaxError(self.id, syntax_errors)

        return used_variables

    def _filter_specs_to_used(
        self,
        used_variables: set,
        template_specs: dict,
    ) -> dict:
        """Filter specs to only include variables used in templates using VariableCollection.

        Uses VariableCollection's native filter_to_used() method.
        Keeps sensitive variables only if they're defined in the template spec or actually used.
        """
        # Build set of variables explicitly defined in template spec
        template_defined_vars = set()
        for section_data in (template_specs or {}).values():
            if isinstance(section_data, dict) and "vars" in section_data:
                template_defined_vars.update(section_data["vars"].keys())

        # Create VariableCollection from template specs
        template_collection = VariableCollection(template_specs)

        # Filter to only used variables (and sensitive ones that are template-defined)
        # We keep sensitive variables that are either:
        # 1. Actually used in template files, OR
        # 2. Explicitly defined in the template spec (even if not yet used)
        variables_to_keep = used_variables | template_defined_vars
        filtered_collection = template_collection.filter_to_used(variables_to_keep, keep_sensitive=False)

        # Convert back to dict format
        filtered_specs = {}
        for section_key, section in filtered_collection.get_sections().items():
            filtered_specs[section_key] = section.to_dict()

        return filtered_specs

    @staticmethod
    def _validate_kind(template_data: dict) -> None:
        """Validate that template has required 'kind' field.

        Args:
            template_data: Parsed YAML data from template.yaml

        Raises:
            ValueError: If 'kind' field is missing
        """
        if not template_data.get("kind"):
            raise TemplateValidationError("Template format error: missing 'kind' field")

    def _validate_variable_definitions(self, used_variables: set[str], merged_specs: dict[str, Any]) -> None:
        """Validate that all variables used in Jinja2 content are defined in the spec."""
        defined_variables = set()
        for section_data in merged_specs.values():
            if "vars" in section_data and isinstance(section_data["vars"], dict):
                defined_variables.update(section_data["vars"].keys())

        undefined_variables = used_variables - defined_variables
        if undefined_variables:
            undefined_list = sorted(undefined_variables)

            # Build file location info for each undefined variable
            file_locations = []
            for var_name in undefined_list:
                if hasattr(self, "_variable_usage_map") and var_name in self._variable_usage_map:
                    files = self._variable_usage_map[var_name]
                    file_locations.append(f"  • {var_name}: {', '.join(files)}")

            error_msg = (
                f"Template validation error in '{self.id}': "
                f"Variables used in template content but not defined in spec:\n"
            )
            if file_locations:
                error_msg += "\n".join(file_locations) + "\n"
            else:
                error_msg += f"{undefined_list}\n"

            error_msg += (
                "\nPlease add these variables to your template's template.yaml spec. "
                "Each variable must have a default value.\n\n"
                "Example:\n"
                "spec:\n"
                "  general:\n"
                "    vars:\n"
            )
            for var_name in undefined_list:
                error_msg += (
                    f"      {var_name}:\n"
                    f"        type: str\n"
                    f"        description: Description for {var_name}\n"
                    f"        default: <your_default_value_here>\n"
                )
            # Only log at DEBUG level - the exception will be displayed to user
            logger.debug(error_msg)
            raise TemplateValidationError(error_msg)

    @staticmethod
    def _create_jinja_env(searchpath: Path) -> Environment:
        """Create sandboxed Jinja2 environment for secure template processing.

        Uses SandboxedEnvironment to prevent code injection vulnerabilities
        when processing untrusted templates. This restricts access to dangerous
        operations while still allowing safe template rendering.

        Returns:
            SandboxedEnvironment configured for template processing.
        """
        # NOTE Use SandboxedEnvironment for security - prevents arbitrary code execution
        return SandboxedEnvironment(
            loader=FileSystemLoader(searchpath),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=False,
        )

    def _generate_autogenerated_values(self, variables: VariableCollection, variable_values: dict) -> None:
        """Generate values for autogenerated variables that are empty.

        Supports both plain and base64-encoded autogenerated values based on
        the autogenerated_base64 flag. Base64 encoding generates random bytes
        and encodes them, which is more suitable for cryptographic keys.
        """
        for section in variables.get_sections().values():
            for var_name, variable in section.variables.items():
                if variable.autogenerated and (variable.value is None or variable.value == ""):
                    length = getattr(variable, "autogenerated_length", 32)
                    use_base64 = getattr(variable, "autogenerated_base64", False)

                    if use_base64:
                        # Generate random bytes and base64 encode
                        # Note: length refers to number of random bytes, not base64 string length
                        random_bytes = secrets.token_bytes(length)
                        generated_value = base64.b64encode(random_bytes).decode("utf-8")
                        logger.debug(
                            f"Auto-generated base64 value for variable '{var_name}' "
                            f"(bytes: {length}, encoded length: {len(generated_value)})"
                        )
                    else:
                        # Generate alphanumeric string
                        alphabet = string.ascii_letters + string.digits
                        generated_value = "".join(secrets.choice(alphabet) for _ in range(length))
                        logger.debug(f"Auto-generated value for variable '{var_name}' (length: {length})")

                    variable_values[var_name] = generated_value

    def _log_render_start(self, debug: bool, variable_values: dict) -> None:
        """Log rendering start information."""
        if debug:
            logger.info(f"Rendering template '{self.id}' in debug mode")
            logger.info(f"Available variables: {sorted(variable_values.keys())}")
            logger.info(f"Variable values: {variable_values}")
        else:
            logger.debug(f"Rendering template '{self.id}' with variables: {variable_values}")

    def _render_jinja2_file(self, template_file, variable_values: dict, _available_vars: set, debug: bool) -> str:
        """Render a single Jinja2 template file."""
        if debug:
            logger.info(f"Rendering Jinja2 template: {template_file.relative_path}")

        template = self.jinja_env.get_template(str(template_file.relative_path))
        rendered_content = template.render(**variable_values)
        rendered_content = self._sanitize_content(rendered_content, template_file.output_path)

        if debug:
            logger.info(f"Successfully rendered: {template_file.relative_path} -> {template_file.output_path}")

        return rendered_content

    def _handle_jinja2_error(
        self,
        e: Exception,
        template_file,
        available_vars: set,
        variable_values: dict,
        debug: bool,
    ) -> None:
        """Handle Jinja2 rendering errors."""
        error_msg, line_num, col, context_lines, suggestions = TemplateErrorHandler.parse_jinja_error(
            e, template_file, self.template_dir, available_vars
        )
        logger.error(f"Error rendering template file {template_file.relative_path}: {error_msg}")

        context = RenderErrorContext(
            file_path=str(template_file.relative_path),
            line_number=line_num,
            column=col,
            context_lines=context_lines,
            variable_context={k: str(v) for k, v in variable_values.items()} if debug else {},
            suggestions=suggestions,
            original_error=e,
        )
        raise TemplateRenderError(message=error_msg, context=context) from e

    def _render_static_file(self, template_file, debug: bool) -> str:
        """Read and return content of a static file."""
        file_path = self.template_dir / template_file.relative_path
        if debug:
            logger.info(f"Copying static file: {template_file.relative_path}")

        try:
            with file_path.open(encoding="utf-8") as f:
                return f.read()
        except OSError as e:
            logger.error(f"Error reading static file {file_path}: {e}")
            context = RenderErrorContext(
                file_path=str(template_file.relative_path),
                suggestions=["Check that the file exists and has read permissions"],
                original_error=e,
            )
            raise TemplateRenderError(
                message=f"Error reading static file: {e}",
                context=context,
            ) from e

    def render(self, variables: VariableCollection, debug: bool = False) -> tuple[dict[str, str], dict[str, Any]]:
        """Render all .j2 files in the template directory.

        Args:
            variables: VariableCollection with values to use for rendering
            debug: Enable debug mode with verbose output

        Returns:
            Tuple of (rendered_files, variable_values) where variable_values includes autogenerated values.
            Empty files (files with only whitespace) are excluded from the returned dict.
        """
        variable_values = variables.get_satisfied_values()
        self._generate_autogenerated_values(variables, variable_values)
        self._log_render_start(debug, variable_values)

        rendered_files = {}
        skipped_files = []
        available_vars = set(variable_values.keys())

        for template_file in self.template_files:
            if template_file.file_type == "j2":
                try:
                    content = self._render_jinja2_file(template_file, variable_values, available_vars, debug)
                    # Skip empty files (only whitespace, empty string, or just YAML document separator)
                    stripped = content.strip()
                    if stripped and stripped != "---":
                        rendered_files[str(template_file.output_path)] = content
                    else:
                        skipped_files.append(str(template_file.output_path))
                        if debug:
                            logger.info(f"Skipping empty file: {template_file.output_path}")
                except (
                    UndefinedError,
                    Jinja2TemplateSyntaxError,
                    Jinja2TemplateNotFound,
                    Jinja2TemplateError,
                ) as e:
                    self._handle_jinja2_error(e, template_file, available_vars, variable_values, debug)
                except Exception as e:
                    logger.error(f"Unexpected error rendering template file {template_file.relative_path}: {e}")
                    context = RenderErrorContext(
                        file_path=str(template_file.relative_path),
                        suggestions=["This is an unexpected error. Please check the template for issues."],
                        original_error=e,
                    )
                    raise TemplateRenderError(
                        message=f"Unexpected rendering error: {e}",
                        context=context,
                    ) from e
            elif template_file.file_type == "static":
                content = self._render_static_file(template_file, debug)
                # Static files are always included, even if empty
                rendered_files[str(template_file.output_path)] = content

        if skipped_files:
            logger.debug(f"Skipped {len(skipped_files)} empty file(s): {', '.join(skipped_files)}")

        return rendered_files, variable_values

    def _sanitize_content(self, content: str, _file_path: Path) -> str:
        """Sanitize rendered content by removing excessive blank lines and trailing whitespace."""
        if not content:
            return content

        lines = [line.rstrip() for line in content.split("\n")]
        sanitized = []
        prev_blank = False

        for line in lines:
            is_blank = not line
            if is_blank and prev_blank:
                continue  # Skip consecutive blank lines
            sanitized.append(line)
            prev_blank = is_blank

        # Remove leading blanks and ensure single trailing newline
        return "\n".join(sanitized).lstrip("\n").rstrip("\n") + "\n"

    @property
    def template_files(self) -> list[TemplateFile]:
        if self.__template_files is None:
            self._collect_template_files()  # Populate self.__template_files
        return self.__template_files

    @property
    def template_specs(self) -> dict:
        """Get the spec section from template YAML data."""
        return self._template_data.get("spec", {})

    @property
    def jinja_env(self) -> Environment:
        if self.__jinja_env is None:
            self.__jinja_env = self._create_jinja_env(self.template_dir)
        return self.__jinja_env

    @property
    def used_variables(self) -> set[str]:
        if self.__used_variables is None:
            self.__used_variables = self._extract_all_used_variables()
        return self.__used_variables

    @property
    def variables(self) -> VariableCollection:
        if self.__variables is None:
            # Warn about unused variables in spec
            self._warn_about_unused_variables(self.template_specs)

            # Validate that all used variables are defined
            self._validate_variable_definitions(self.used_variables, self.template_specs)

            # Filter specs to only used variables
            filtered_specs = self._filter_specs_to_used(
                self.used_variables,
                self.template_specs,
            )

            self.__variables = VariableCollection(filtered_specs)
        return self.__variables

    @property
    def status(self) -> str:
        """Get the status of the template.

        Returns:
            Status string: 'published' or 'draft'

        Note:
            The 'invalid' status is reserved for future use when template validation
            is implemented without impacting list command performance.
        """
        # Check if template is marked as draft in metadata
        if self.metadata.draft:
            return TEMPLATE_STATUS_DRAFT

        # Template is published (valid and not draft)
        return TEMPLATE_STATUS_PUBLISHED
