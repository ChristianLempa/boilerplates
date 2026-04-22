from __future__ import annotations

import json
import logging
from pathlib import Path

from .config import ConfigManager
from .exceptions import DuplicateTemplateError, LibraryError, TemplateNotFoundError
from .template import normalize_template_slug

logger = logging.getLogger(__name__)

# Qualified ID format: "template_id.library_name"
QUALIFIED_ID_PARTS = 2
TEMPLATE_MANIFEST_FILENAME = "template.json"


class Library:
    """Represents a single library with a specific path."""

    def __init__(self, name: str, path: Path, priority: int = 0, library_type: str = "git") -> None:
        """Initialize a library instance.

        Args:
          name: Display name for the library
          path: Path to the library directory
          priority: Priority for library lookup (higher = checked first)
          library_type: Type of library ("git" or "static")
        """
        if library_type not in ("git", "static"):
            raise ValueError(f"Invalid library type: {library_type}. Must be 'git' or 'static'.")

        self.name = name
        self.path = path
        self.priority = priority  # Higher priority = checked first
        self.library_type = library_type

    def _is_template_draft(self, template_path: Path) -> bool:
        """Check if a template is marked as draft."""
        template_file = template_path / TEMPLATE_MANIFEST_FILENAME
        if not template_file.exists():
            return False

        try:
            with template_file.open(encoding="utf-8") as f:
                data = json.load(f) or {}
            return bool(data.get("metadata", {}).get("draft", False))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Error checking draft status for {template_path}: {e}")
            return False

    @staticmethod
    def _has_template_manifest(template_path: Path) -> bool:
        """Check if a directory contains the supported template manifest."""
        return template_path.is_dir() and (template_path / TEMPLATE_MANIFEST_FILENAME).exists()

    @staticmethod
    def _load_template_id(template_path: Path) -> str:
        """Load the canonical template ID from the manifest slug.

        Falls back to the directory name when manifest metadata is unreadable.
        """
        manifest_path = template_path / TEMPLATE_MANIFEST_FILENAME
        if manifest_path.exists():
            try:
                with manifest_path.open(encoding="utf-8") as file_handle:
                    data = json.load(file_handle) or {}
                slug = str(data.get("slug", "")).strip()
                kind = str(data.get("kind", "")).strip()
                if slug:
                    return normalize_template_slug(slug, kind)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Error reading template slug for %s: %s", template_path, exc)

        return template_path.name

    def find_by_id(self, module_name: str, template_id: str) -> tuple[Path, str]:
        """Find a template by its ID in this library.

        Args:
            module_name: The module name (e.g., 'compose', 'terraform')
            template_id: The template ID to find

        Returns:
            Path to the template directory if found

        Raises:
            FileNotFoundError: If the template ID is not found in this library or is marked as draft
        """
        logger.debug(f"Looking for template '{template_id}' in module '{module_name}' in library '{self.name}'")

        module_path = self.path / module_name
        if not module_path.is_dir():
            raise TemplateNotFoundError(template_id, module_name)

        try:
            for item in module_path.iterdir():
                if not self._has_template_manifest(item) or self._is_template_draft(item):
                    continue
                resolved_id = self._load_template_id(item)
                if resolved_id == template_id:
                    logger.debug("Found template '%s' at: %s", template_id, item)
                    return item, self.name
        except PermissionError as exc:
            raise LibraryError(
                f"Permission denied accessing module '{module_name}' in library '{self.name}': {exc}"
            ) from exc

        raise TemplateNotFoundError(template_id, module_name)

    def find(self, module_name: str, sort_results: bool = False) -> list[tuple[Path, str]]:
        """Find templates in this library for a specific module.

        Excludes templates marked as draft.

        Args:
            module_name: The module name (e.g., 'compose', 'terraform')
            sort_results: Whether to return results sorted alphabetically

        Returns:
            List of Path objects representing template directories (excluding drafts)

        Raises:
            FileNotFoundError: If the module directory is not found in this library
        """
        logger.debug(f"Looking for templates in module '{module_name}' in library '{self.name}'")

        # Build the path to the module directory
        module_path = self.path / module_name

        # Check if the module directory exists
        if not module_path.is_dir():
            raise LibraryError(f"Module '{module_name}' not found in library '{self.name}'")

        # Track seen IDs to detect duplicates within this library
        seen_ids = {}
        template_dirs = []
        try:
            for item in module_path.iterdir():
                has_template = self._has_template_manifest(item)
                if has_template and not self._is_template_draft(item):
                    template_id = self._load_template_id(item)

                    # Check for duplicate within same library
                    if template_id in seen_ids:
                        raise DuplicateTemplateError(template_id, self.name)

                    seen_ids[template_id] = True
                    template_dirs.append((item, self.name))
                elif has_template:
                    logger.debug(f"Skipping draft template: {item.name}")
        except PermissionError as e:
            raise LibraryError(
                f"Permission denied accessing module '{module_name}' in library '{self.name}': {e}"
            ) from e

        # Sort if requested
        if sort_results:
            template_dirs.sort(key=lambda x: x[0].name.lower())

        logger.debug(f"Found {len(template_dirs)} templates in module '{module_name}'")
        return template_dirs


class LibraryManager:
    """Manages multiple libraries and provides methods to find templates."""

    def __init__(self) -> None:
        """Initialize LibraryManager with git-based libraries from config."""
        self.config = ConfigManager()
        self.libraries = self._load_libraries_from_config()

    def _resolve_git_library_path(self, name: str, lib_config: dict, libraries_path: Path) -> Path:
        """Resolve path for a git-based library."""
        directory = lib_config.get("directory", ".")
        library_base = libraries_path / name
        if directory and directory != ".":
            configured_path = library_base / directory
            fallback_path = self._fallback_template_root(configured_path)
            return fallback_path or configured_path
        return library_base

    def _resolve_static_library_path(self, name: str, lib_config: dict) -> Path | None:
        """Resolve path for a static library."""
        path_str = lib_config.get("path")
        if not path_str:
            logger.warning(f"Static library '{name}' has no path configured")
            return None

        library_path = Path(path_str).expanduser()
        if not library_path.is_absolute():
            library_path = (self.config.config_path.parent / library_path).resolve()
        fallback_path = self._fallback_template_root(library_path)
        return fallback_path or library_path

    @staticmethod
    def _looks_like_template_root(path: Path) -> bool:
        """Check whether a path looks like the root of a templates repository."""
        if not path.is_dir():
            return False
        try:
            return any(item.is_dir() for item in path.iterdir())
        except OSError:
            return False

    def _fallback_template_root(self, path: Path) -> Path | None:
        """Resolve common old-style /library paths to the actual template repo root."""
        if path.exists():
            if self._looks_like_template_root(path):
                return path
            if path.name == "library" and self._looks_like_template_root(path.parent):
                logger.info("Using parent directory '%s' as template root instead of '%s'", path.parent, path)
                return path.parent
            return None

        if path.name == "library" and self._looks_like_template_root(path.parent):
            logger.info("Using parent directory '%s' as template root instead of missing '%s'", path.parent, path)
            return path.parent

        return None

    def _warn_missing_library(self, name: str, library_path: Path, lib_type: str) -> None:
        """Log warning about missing library."""
        if lib_type == "git":
            logger.warning(
                f"Library '{name}' not found at {library_path}. Run 'boilerplates repo update' to sync libraries."
            )
        else:
            logger.warning(f"Static library '{name}' not found at {library_path}")

    def _load_libraries_from_config(self) -> list[Library]:
        """Load libraries from configuration.

        Returns:
            List of Library instances
        """
        libraries = []
        libraries_path = self.config.get_libraries_path()
        library_configs = self.config.get_libraries()

        for i, lib_config in enumerate(library_configs):
            # Skip disabled libraries
            if not lib_config.get("enabled", True):
                logger.debug(f"Skipping disabled library: {lib_config.get('name')}")
                continue

            name = lib_config.get("name")
            lib_type = lib_config.get("type", "git")

            # Resolve library path based on type
            if lib_type == "git":
                library_path = self._resolve_git_library_path(name, lib_config, libraries_path)
            elif lib_type == "static":
                library_path = self._resolve_static_library_path(name, lib_config)
                if not library_path:
                    continue
            else:
                logger.warning(f"Unknown library type '{lib_type}' for library '{name}'")
                continue

            # Check if library path exists
            if not library_path.exists():
                self._warn_missing_library(name, library_path, lib_type)
                continue

            # Create Library instance with priority based on order
            priority = len(library_configs) - i
            libraries.append(
                Library(
                    name=name,
                    path=library_path,
                    priority=priority,
                    library_type=lib_type,
                )
            )
            logger.debug(f"Loaded {lib_type} library '{name}' from {library_path} with priority {priority}")

        if not libraries:
            logger.warning("No libraries loaded. Run 'boilerplates repo update' to sync libraries.")

        return libraries

    def find_by_id(self, module_name: str, template_id: str) -> tuple[Path, str] | None:
        """Find a template by its ID across all libraries.

        Supports both simple IDs and qualified IDs (template.library format).

        Args:
            module_name: The module name (e.g., 'compose', 'terraform')
            template_id: The template ID to find (simple or qualified)

        Returns:
            Tuple of (template_path, library_name) if found, None otherwise
        """
        logger.debug(f"Searching for template '{template_id}' in module '{module_name}' across all libraries")

        # Check if this is a qualified ID (contains '.')
        if "." in template_id:
            parts = template_id.rsplit(".", 1)
            if len(parts) == QUALIFIED_ID_PARTS:
                base_id, requested_lib = parts
                logger.debug(f"Parsing qualified ID: base='{base_id}', library='{requested_lib}'")

                # Try to find in the specific library
                for library in self.libraries:
                    if library.name == requested_lib:
                        try:
                            template_path, lib_name = library.find_by_id(module_name, base_id)
                            logger.debug(f"Found template '{base_id}' in library '{requested_lib}'")
                            return template_path, lib_name
                        except TemplateNotFoundError:
                            logger.debug(f"Template '{base_id}' not found in library '{requested_lib}'")
                            return None

                logger.debug(f"Library '{requested_lib}' not found")
                return None

        # Simple ID - search by priority
        for library in sorted(self.libraries, key=lambda x: x.priority, reverse=True):
            try:
                template_path, lib_name = library.find_by_id(module_name, template_id)
                logger.debug(f"Found template '{template_id}' in library '{library.name}'")
                return template_path, lib_name
            except TemplateNotFoundError:
                # Continue searching in next library
                continue

        logger.debug(f"Template '{template_id}' not found in any library")
        return None

    def find(self, module_name: str, sort_results: bool = False) -> list[tuple[Path, str, bool]]:
        """Find templates across all libraries for a specific module.

        Handles duplicates by qualifying IDs with library names when needed.

        Args:
            module_name: The module name (e.g., 'compose', 'terraform')
            sort_results: Whether to return results sorted alphabetically

        Returns:
            List of tuples (template_path, library_name, needs_qualification)
            where needs_qualification is True if the template ID appears in multiple libraries
        """
        logger.debug(f"Searching for templates in module '{module_name}' across all libraries")

        all_templates = []

        # Collect templates from all libraries
        for library in sorted(self.libraries, key=lambda x: x.priority, reverse=True):
            try:
                templates = library.find(module_name, sort_results=False)
                all_templates.extend(templates)
                logger.debug(f"Found {len(templates)} templates in library '{library.name}'")
            except (LibraryError, DuplicateTemplateError) as e:
                # DuplicateTemplateError from library.find() should propagate up
                if isinstance(e, DuplicateTemplateError):
                    raise
                logger.debug(f"Module '{module_name}' not found in library '{library.name}'")
                continue

        # Track template IDs and their libraries to detect cross-library duplicates
        id_to_occurrences = {}
        for template_path, library_name in all_templates:
            template_id = template_path.name
            if template_id not in id_to_occurrences:
                id_to_occurrences[template_id] = []
            id_to_occurrences[template_id].append((template_path, library_name))

        # Build result with qualification markers for duplicates
        result = []
        for template_id, occurrences in id_to_occurrences.items():
            if len(occurrences) > 1:
                # Duplicate across libraries - mark for qualified IDs
                lib_names = ", ".join(lib for _, lib in occurrences)
                logger.info(f"Template '{template_id}' found in multiple libraries: {lib_names}. Using qualified IDs.")
                for template_path, library_name in occurrences:
                    # Mark that this ID needs qualification
                    result.append((template_path, library_name, True))
            else:
                # Unique template - no qualification needed
                template_path, library_name = occurrences[0]
                result.append((template_path, library_name, False))

        # Sort if requested
        if sort_results:
            result.sort(key=lambda x: x[0].name.lower())

        logger.debug(f"Found {len(result)} templates total")
        return result
