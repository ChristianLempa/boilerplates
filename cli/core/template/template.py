from __future__ import annotations

import base64
import json
import logging
import os
import re
import secrets
import string
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, meta
from jinja2.exceptions import TemplateError as Jinja2TemplateError
from jinja2.exceptions import TemplateNotFound as Jinja2TemplateNotFound
from jinja2.exceptions import TemplateSyntaxError as Jinja2TemplateSyntaxError
from jinja2.exceptions import UndefinedError
from jinja2.sandbox import SandboxedEnvironment

from ..exceptions import RenderErrorContext, TemplateLoadError, TemplateRenderError, TemplateValidationError
from .variable_collection import VariableCollection

logger = logging.getLogger(__name__)

TEMPLATE_MANIFEST_FILENAME = "template.json"
LEGACY_TEMPLATE_FILENAMES = ("template.yaml", "template.yml")
TEMPLATE_FILES_DIRNAME = "files"
VARIABLE_START = "<<"
VARIABLE_END = ">>"
BLOCK_START = "<%"
BLOCK_END = "%>"
COMMENT_START = "<#"
COMMENT_END = "#>"


def normalize_template_slug(slug: str, kind: str | None = None) -> str:
    """Normalize a manifest slug for CLI use.

    If the slug ends with "-<kind>", remove that redundant suffix.
    Example: "portainer-compose" -> "portainer" for kind "compose".
    """
    normalized_slug = str(slug).strip()
    normalized_kind = str(kind or "").strip()

    if not normalized_slug:
        return normalized_slug

    suffix = f"-{normalized_kind}" if normalized_kind else ""
    if suffix and normalized_slug.endswith(suffix):
        return normalized_slug[: -len(suffix)]

    return normalized_slug


class TemplateErrorHandler:
    """Parses Jinja rendering errors into user-friendly context."""

    @staticmethod
    def extract_error_context(file_path: Path, line_number: int | None, context_size: int = 3) -> list[str]:
        """Extract lines around a rendering error."""
        if not line_number or not file_path.exists():
            return []

        try:
            with file_path.open(encoding="utf-8") as file_handle:
                lines = file_handle.readlines()
        except OSError:
            return []

        start_line = max(0, line_number - context_size - 1)
        end_line = min(len(lines), line_number + context_size)

        context = []
        for index in range(start_line, end_line):
            display_line = index + 1
            marker = ">>>" if display_line == line_number else "   "
            context.append(f"{marker} {display_line:4d} | {lines[index].rstrip()}")
        return context

    @staticmethod
    def get_common_suggestions(error_msg: str, available_vars: set[str]) -> list[str]:
        """Build action-oriented suggestions for common rendering failures."""
        suggestions = []
        error_lower = error_msg.lower()

        if "undefined" in error_lower or "is not defined" in error_lower:
            var_match = re.search(r"'([^']+)'.*is undefined", error_msg)
            if not var_match:
                var_match = re.search(r"'([^']+)'.*is not defined", error_msg)

            if var_match:
                undefined_var = var_match.group(1)
                suggestions.append(f"Variable '{undefined_var}' is not defined in template.json")
                similar = [
                    candidate
                    for candidate in available_vars
                    if undefined_var.lower() in candidate.lower() or candidate.lower() in undefined_var.lower()
                ]
                if similar:
                    suggestions.append(f"Did you mean: {', '.join(sorted(similar)[:5])}")
                suggestions.append("Declare the variable under variables[].items in template.json")
                suggestions.append(f"Or make it optional with << {undefined_var} | default('value') >>")
            else:
                suggestions.append("Check that every rendered variable is declared in template.json")
        elif "unexpected" in error_lower or "expected" in error_lower:
            suggestions.append("Check template control-flow syntax with the new delimiters")
            suggestions.append("Use <% %> for blocks, << >> for variables, and <# #> for comments")
        elif "not found" in error_lower or "does not exist" in error_lower:
            suggestions.append("Check included/imported files relative to the template's files/ directory")
        else:
            suggestions.append("Inspect template syntax and variable usage")

        if not suggestions:
            suggestions.append("Enable --log-level DEBUG for more detail")

        return suggestions

    @classmethod
    def parse_jinja_error(
        cls,
        error: Exception,
        template_file: TemplateFile,
        files_dir: Path,
        available_vars: set[str],
    ) -> tuple[str, int | None, int | None, list[str], list[str]]:
        """Parse a Jinja exception into structured display data."""
        error_message = str(error)
        line_number = getattr(error, "lineno", None)
        file_path = files_dir / template_file.relative_path
        context_lines = cls.extract_error_context(file_path, line_number)
        suggestions = cls.get_common_suggestions(error_message, available_vars)

        if isinstance(error, UndefinedError):
            error_message = f"Undefined variable: {error}"
        elif isinstance(error, Jinja2TemplateSyntaxError):
            error_message = f"Template syntax error: {error}"
        elif isinstance(error, Jinja2TemplateNotFound):
            error_message = f"Template file not found: {error}"

        return error_message, line_number, None, context_lines, suggestions


@dataclass
class TemplateFile:
    """Represents a renderable template file."""

    relative_path: Path
    output_path: Path


@dataclass
class TemplateVersionMetadata:
    """Structured version metadata extracted from template.json."""

    name: str = ""
    source_dep_name: str = ""
    source_dep_version: str = ""
    source_dep_digest: str = ""
    upstream_ref: str = ""
    notes: str = ""

    def __bool__(self) -> bool:
        """Treat the version as present for display when a name exists."""
        return bool(self.name)

    def __str__(self) -> str:
        """Render the user-facing version label."""
        return self.name

    @classmethod
    def from_metadata(cls, metadata: dict[str, Any]) -> TemplateVersionMetadata:
        """Parse the optional metadata.version object."""
        version_data = metadata.get("version")
        if version_data is None:
            return cls()

        if not isinstance(version_data, dict):
            raise TemplateValidationError("Template format error: 'metadata.version' must be an object")

        return cls(
            name=str(version_data.get("name", "")).strip(),
            source_dep_name=str(version_data.get("source_dep_name", "")).strip(),
            source_dep_version=str(version_data.get("source_dep_version", "")).strip(),
            source_dep_digest=str(version_data.get("source_dep_digest", "")).strip(),
            upstream_ref=str(version_data.get("upstream_ref", "")).strip(),
            notes=str(version_data.get("notes", "")).rstrip("\n"),
        )


@dataclass
class TemplateMetadata:
    """Typed template metadata extracted from template.json."""

    name: str
    description: str
    author: str
    date: str
    version: TemplateVersionMetadata = field(default_factory=TemplateVersionMetadata)
    module: str = ""
    tags: list[str] = field(default_factory=list)
    library: str = "unknown"
    library_type: str = "git"
    draft: bool = False
    icon: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        template_data: dict[str, Any],
        library_name: str | None = None,
        library_type: str = "git",
    ) -> None:
        metadata = template_data.get("metadata")
        if not isinstance(metadata, dict):
            raise TemplateValidationError("Template format error: missing 'metadata' object in template.json")

        self.name = str(metadata.get("name", "")).strip()
        self.description = str(metadata.get("description", "")).rstrip("\n")
        self.author = str(metadata.get("author", "")).strip()
        self.date = str(metadata.get("date", "")).strip()
        self.version = TemplateVersionMetadata.from_metadata(metadata)
        self.module = str(template_data.get("kind", "")).strip()
        self.tags = metadata.get("tags", []) if isinstance(metadata.get("tags", []), list) else []
        self.library = library_name or "unknown"
        self.library_type = library_type
        self.draft = bool(metadata.get("draft", False))
        self.icon = metadata.get("icon", {}) if isinstance(metadata.get("icon"), dict) else {}


class Template:
    """Loads, validates, and renders template.json-based templates."""

    def __init__(self, template_dir: Path, library_name: str, library_type: str = "git") -> None:
        self.template_dir = template_dir
        self.directory_id = template_dir.name
        self.id = template_dir.name
        self.original_id = template_dir.name
        self.library_name = library_name
        self.library_type = library_type

        self.__jinja_env: Environment | None = None
        self.__used_variables: set[str] | None = None
        self.__variables: VariableCollection | None = None
        self.__template_files: list[TemplateFile] | None = None

        try:
            manifest_path = self._find_manifest_file()
            with manifest_path.open(encoding="utf-8") as file_handle:
                self._template_data = json.load(file_handle)

            if not isinstance(self._template_data, dict):
                raise TemplateValidationError("Template format error: template.json must contain a JSON object")

            self.metadata = TemplateMetadata(self._template_data, library_name, library_type)
            self._validate_kind(self._template_data)
            self.slug = self._get_template_slug(self._template_data, self.directory_id)
            self.id = self.slug
            self.original_id = self.slug

            self.files_dir = self.template_dir / TEMPLATE_FILES_DIRNAME
            if not self.files_dir.is_dir():
                raise TemplateValidationError(
                    f"Template '{self.id}' is missing required '{TEMPLATE_FILES_DIRNAME}/' directory"
                )

            self._validate_template_manifest()
            logger.info("Loaded template '%s' (version=%s)", self.id, self.metadata.version or "unknown")
        except (json.JSONDecodeError, TemplateValidationError, FileNotFoundError) as exc:
            logger.error("Error loading template from %s: %s", template_dir, exc)
            raise TemplateLoadError(f"Error loading template from {template_dir}: {exc}") from exc
        except OSError as exc:
            logger.error("File I/O error loading template %s: %s", template_dir, exc)
            raise TemplateLoadError(f"File I/O error loading template from {template_dir}: {exc}") from exc

    def set_qualified_id(self, library_name: str | None = None) -> None:
        """Set a qualified template ID when duplicates exist across libraries."""
        lib_name = library_name or self.library_name
        self.id = f"{self.original_id}.{lib_name}"

    def _find_manifest_file(self) -> Path:
        """Locate template.json and reject legacy template manifests."""
        manifest_path = self.template_dir / TEMPLATE_MANIFEST_FILENAME
        if manifest_path.exists():
            return manifest_path

        for legacy_name in LEGACY_TEMPLATE_FILENAMES:
            legacy_path = self.template_dir / legacy_name
            if legacy_path.exists():
                raise TemplateValidationError(
                    "Legacy template manifests are incompatible with boilerplates 0.2.0. "
                    f"Replace '{legacy_name}' with '{TEMPLATE_MANIFEST_FILENAME}' and move renderable files into "
                    f"'{TEMPLATE_FILES_DIRNAME}/'."
                )

        raise FileNotFoundError(f"Main template file ({TEMPLATE_MANIFEST_FILENAME}) not found in {self.template_dir}")

    def _validate_template_manifest(self) -> None:
        """Validate required top-level manifest structure."""
        variables = self._template_data.get("variables", [])
        if not isinstance(variables, list):
            raise TemplateValidationError("Template format error: 'variables' must be a list")

    @staticmethod
    def _validate_kind(template_data: dict[str, Any]) -> None:
        """Validate presence of the template kind."""
        if not template_data.get("kind"):
            raise TemplateValidationError("Template format error: missing 'kind' field")

    @staticmethod
    def _get_template_slug(template_data: dict[str, Any], fallback: str) -> str:
        """Resolve the canonical template ID from the manifest slug."""
        manifest_slug = str(template_data.get("slug", "")).strip()
        kind = str(template_data.get("kind", "")).strip()
        if not manifest_slug:
            return fallback
        return normalize_template_slug(manifest_slug, kind)

    @staticmethod
    def _create_jinja_env(search_path: Path) -> SandboxedEnvironment:
        """Create the custom-delimiter Jinja environment for template rendering."""
        return SandboxedEnvironment(
            loader=FileSystemLoader(search_path),
            autoescape=False,
            variable_start_string=VARIABLE_START,
            variable_end_string=VARIABLE_END,
            block_start_string=BLOCK_START,
            block_end_string=BLOCK_END,
            comment_start_string=COMMENT_START,
            comment_end_string=COMMENT_END,
            keep_trailing_newline=True,
            trim_blocks=False,
            lstrip_blocks=False,
        )

    def _collect_template_files(self) -> None:
        """Collect every renderable file under files/."""
        template_files: list[TemplateFile] = []

        for root, _, files in os.walk(self.files_dir):
            for filename in files:
                absolute_path = Path(root) / filename
                relative_path = absolute_path.relative_to(self.files_dir)
                template_files.append(
                    TemplateFile(
                        relative_path=relative_path,
                        output_path=relative_path,
                    )
                )

        template_files.sort(key=lambda item: str(item.relative_path))
        self.__template_files = template_files

    def _extract_all_used_variables(self) -> set[str]:
        """Extract undeclared variables from all files under files/."""
        used_variables: set[str] = set()
        syntax_errors = []
        self._variable_usage_map: dict[str, list[str]] = {}

        for template_file in self.template_files:
            file_path = self.files_dir / template_file.relative_path
            try:
                content = file_path.read_text(encoding="utf-8")
                ast = self.jinja_env.parse(content)
                file_variables = meta.find_undeclared_variables(ast)
                used_variables.update(file_variables)
                for variable_name in file_variables:
                    self._variable_usage_map.setdefault(variable_name, []).append(str(template_file.relative_path))
            except Jinja2TemplateSyntaxError as exc:
                syntax_errors.append(f"{template_file.relative_path}:{exc.lineno}: {exc.message}")
            except OSError as exc:
                raise TemplateValidationError(
                    f"Failed to read template file '{template_file.relative_path}': {exc}"
                ) from exc

        if syntax_errors:
            raise TemplateValidationError("Template syntax validation failed:\n" + "\n".join(sorted(syntax_errors)))

        return used_variables

    @staticmethod
    def _merge_item_config(item_data: dict[str, Any]) -> dict[str, Any]:
        """Flatten manifest item fields into the VariableCollection runtime shape."""
        if not isinstance(item_data, dict):
            raise TemplateValidationError("Variable items must be objects")

        if "name" not in item_data:
            raise TemplateValidationError("Variable item missing required 'name' field")

        item_type = item_data.get("type", "str")
        item_config = item_data.get("config", {})
        if item_config is not None and not isinstance(item_config, dict):
            raise TemplateValidationError(f"Variable '{item_data['name']}' config must be an object")

        normalized = {"type": item_type}
        field_map = {
            "default": "default",
            "value": "value",
            "required": "required",
            "needs": "needs",
            "extra": "extra",
        }
        for source_key, target_key in field_map.items():
            if source_key in item_data:
                normalized[target_key] = item_data[source_key]

        description = item_data.get("description") or item_data.get("title")
        if description is not None:
            normalized["description"] = description
        if "title" in item_data:
            normalized["prompt"] = item_data["title"]

        config_value = item_data.get("config", item_config)
        if config_value:
            normalized["config"] = config_value

        return normalized

    def _normalize_manifest_variables(self) -> dict[str, Any]:
        """Convert variables[].items manifest structure into VariableCollection format."""
        spec: dict[str, Any] = {}

        for group_data in self._template_data.get("variables", []):
            if not isinstance(group_data, dict):
                raise TemplateValidationError("Variable groups must be objects")
            if "name" not in group_data:
                raise TemplateValidationError("Variable group missing required 'name' field")
            if "title" not in group_data:
                raise TemplateValidationError(f"Variable group '{group_data['name']}' missing required 'title' field")

            group_name = group_data["name"]
            items = group_data.get("items")
            if not isinstance(items, list):
                raise TemplateValidationError(f"Variable group '{group_name}' must define an 'items' array")

            section_data: dict[str, Any] = {
                "title": group_data["title"],
                "vars": {},
            }
            for optional_key in ("description", "toggle", "needs"):
                if optional_key in group_data:
                    section_data[optional_key] = group_data[optional_key]

            for item_data in items:
                normalized_item = self._merge_item_config(item_data)
                variable_name = item_data["name"]
                section_data["vars"][variable_name] = normalized_item

            spec[group_name] = section_data

        return spec

    def _validate_variable_definitions(self, used_variables: set[str], spec: dict[str, Any]) -> None:
        """Validate that all rendered variables are declared in the manifest."""
        defined_variables = set()
        for section_data in spec.values():
            defined_variables.update((section_data.get("vars") or {}).keys())

        undefined_variables = used_variables - defined_variables
        if not undefined_variables:
            return

        undefined_list = sorted(undefined_variables)
        file_locations = []
        for variable_name in undefined_list:
            if variable_name in getattr(self, "_variable_usage_map", {}):
                locations = ", ".join(self._variable_usage_map[variable_name])
                file_locations.append(f"  - {variable_name}: {locations}")

        error_lines = [
            f"Template validation error in '{self.id}': variables used in files/ but not declared in template.json."
        ]
        if file_locations:
            error_lines.extend(file_locations)
        else:
            error_lines.append(", ".join(undefined_list))
        error_lines.extend(
            [
                "",
                "Declare missing variables under variables[].items in template.json.",
                "Example:",
                "{",
                '  "variables": [',
                "    {",
                '      "name": "general",',
                '      "title": "General",',
                '      "items": [',
                '        { "name": "missing_var", "type": "str", "title": "Missing var" }',
                "      ]",
                "    }",
                "  ]",
                "}",
            ]
        )
        raise TemplateValidationError("\n".join(error_lines))

    def _generate_autogenerated_values(
        self,
        variables: VariableCollection,
        variable_values: dict[str, Any],
    ) -> None:
        """Populate autogenerated values for empty variables."""
        for variable in variables._variable_map.values():
            if not variable.autogenerated:
                continue

            current_value = variable_values.get(variable.name)
            if current_value not in (None, ""):
                continue

            length = getattr(variable, "autogenerated_length", 32)
            autogenerated_config = getattr(variable, "autogenerated_config", None)
            if getattr(variable, "autogenerated_base64", False):
                bytes_length = autogenerated_config.bytes_or_default() if autogenerated_config else length
                generated_value = base64.b64encode(secrets.token_bytes(bytes_length)).decode("utf-8")
            else:
                alphabet = (
                    "".join(autogenerated_config.characters)
                    if autogenerated_config and autogenerated_config.characters
                    else string.ascii_letters + string.digits
                )
                generated_value = "".join(secrets.choice(alphabet) for _ in range(length))

            variable_values[variable.name] = generated_value

    def _sanitize_content(self, content: str) -> str:
        """Normalize rendered text output."""
        if not content:
            return content

        lines = [line.rstrip() for line in content.split("\n")]
        sanitized: list[str] = []
        previous_blank = False

        for line in lines:
            is_blank = not line
            if is_blank and previous_blank:
                continue
            sanitized.append(line)
            previous_blank = is_blank

        return "\n".join(sanitized).lstrip("\n").rstrip("\n") + "\n"

    def _handle_render_error(
        self,
        error: Exception,
        template_file: TemplateFile,
        available_vars: set[str],
        variable_values: dict[str, Any],
        debug: bool,
    ) -> None:
        """Convert Jinja errors into TemplateRenderError."""
        error_message, line_number, column, context_lines, suggestions = TemplateErrorHandler.parse_jinja_error(
            error,
            template_file,
            self.files_dir,
            available_vars,
        )
        context = RenderErrorContext(
            file_path=str(template_file.relative_path),
            line_number=line_number,
            column=column,
            context_lines=context_lines,
            variable_context={key: str(value) for key, value in variable_values.items()} if debug else {},
            suggestions=suggestions,
            original_error=error,
        )
        raise TemplateRenderError(message=error_message, context=context) from error

    def render(self, variables: VariableCollection, debug: bool = False) -> tuple[dict[str, str], dict[str, Any]]:
        """Render every file under files/ using the new delimiter set."""
        variable_values = variables.get_satisfied_values()
        self._generate_autogenerated_values(variables, variable_values)

        rendered_files: dict[str, str] = {}
        available_vars = set(variable_values.keys())

        for template_file in self.template_files:
            try:
                template = self.jinja_env.get_template(str(template_file.relative_path))
                rendered_content = template.render(**variable_values)
                rendered_content = self._sanitize_content(rendered_content)
            except (
                UndefinedError,
                Jinja2TemplateSyntaxError,
                Jinja2TemplateNotFound,
                Jinja2TemplateError,
            ) as exc:
                self._handle_render_error(exc, template_file, available_vars, variable_values, debug)
            except Exception as exc:
                raise TemplateRenderError(
                    message=f"Unexpected rendering error: {exc}",
                    context=RenderErrorContext(
                        file_path=str(template_file.relative_path),
                        original_error=exc,
                        suggestions=["Check the template content and variable values."],
                    ),
                ) from exc

            stripped = rendered_content.strip()
            if stripped and stripped != "---":
                rendered_files[str(template_file.output_path)] = rendered_content

        return rendered_files, variable_values

    @property
    def template_files(self) -> list[TemplateFile]:
        if self.__template_files is None:
            self._collect_template_files()
        return self.__template_files

    @property
    def jinja_env(self) -> Environment:
        if self.__jinja_env is None:
            self.__jinja_env = self._create_jinja_env(self.files_dir)
        return self.__jinja_env

    @property
    def used_variables(self) -> set[str]:
        if self.__used_variables is None:
            self.__used_variables = self._extract_all_used_variables()
        return self.__used_variables

    @property
    def variables(self) -> VariableCollection:
        if self.__variables is None:
            spec = self._normalize_manifest_variables()
            self._validate_variable_definitions(self.used_variables, spec)
            self.__variables = VariableCollection(spec)
            self.__variables.sort_sections()
        return self.__variables
