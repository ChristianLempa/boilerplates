from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Union
import logging

from .variable import Variable
from .section import VariableSection

logger = logging.getLogger(__name__)


class VariableCollection:
    """Manages variables grouped by sections and builds Jinja context."""

    def __init__(self, spec: dict[str, Any]) -> None:
        """Initialize VariableCollection from a specification dictionary.

        Args:
            spec: Dictionary containing the complete variable specification structure
                  Expected format (as used in compose.py):
                  {
                    "section_key": {
                      "title": "Section Title",
                      "prompt": "Optional prompt text",
                      "toggle": "optional_toggle_var_name",
                      "description": "Optional description",
                      "vars": {
                        "var_name": {
                          "description": "Variable description",
                          "type": "str",
                          "default": "default_value",
                          ...
                        }
                      }
                    }
                  }
        """
        if not isinstance(spec, dict):
            raise ValueError("Spec must be a dictionary")

        self._sections: Dict[str, VariableSection] = {}
        # NOTE: The _variable_map provides a flat, O(1) lookup for any variable by its name,
        # avoiding the need to iterate through sections. It stores references to the same
        # Variable objects contained in the _set structure.
        self._variable_map: Dict[str, Variable] = {}
        self._initialize_sections(spec)
        # Validate dependencies after all sections are loaded
        self._validate_dependencies()

    def _initialize_sections(self, spec: dict[str, Any]) -> None:
        """Initialize sections from the spec."""
        for section_key, section_data in spec.items():
            if not isinstance(section_data, dict):
                continue

            section = self._create_section(section_key, section_data)
            # Guard against None from empty YAML sections (vars: with no content)
            vars_data = section_data.get("vars") or {}
            self._initialize_variables(section, vars_data)
            self._sections[section_key] = section

        # Validate all variable names are unique across sections
        self._validate_unique_variable_names()

    def _create_section(self, key: str, data: dict[str, Any]) -> VariableSection:
        """Create a VariableSection from data."""
        # Build section init data with only explicitly provided fields
        # This prevents None values from overriding module spec values during merge
        section_init_data = {
            "key": key,
            "title": data.get("title", key.replace("_", " ").title()),
        }

        # Only add optional fields if explicitly provided in the source data
        if "description" in data:
            section_init_data["description"] = data["description"]
        if "toggle" in data:
            section_init_data["toggle"] = data["toggle"]
        if "required" in data:
            section_init_data["required"] = data["required"]
        elif key == "general":
            section_init_data["required"] = True
        if "needs" in data:
            section_init_data["needs"] = data["needs"]

        return VariableSection(section_init_data)

    def _initialize_variables(
        self, section: VariableSection, vars_data: dict[str, Any]
    ) -> None:
        """Initialize variables for a section."""
        # Guard against None from empty YAML sections
        if vars_data is None:
            vars_data = {}

        for var_name, var_data in vars_data.items():
            var_init_data = {"name": var_name, "parent_section": section, **var_data}
            variable = Variable(var_init_data)
            section.variables[var_name] = variable
            # NOTE: Populate the direct lookup map for efficient access.
            self._variable_map[var_name] = variable

        # Validate toggle variable after all variables are added
        self._validate_section_toggle(section)
        # TODO: Add more section-level validation:
        #   - Validate that required sections have at least one non-toggle variable
        #   - Validate that enum variables have non-empty options lists
        #   - Validate that variable names follow naming conventions (e.g., lowercase_with_underscores)
        #   - Validate that default values are compatible with their type definitions

    def _validate_unique_variable_names(self) -> None:
        """Validate that all variable names are unique across all sections."""
        var_to_sections: Dict[str, List[str]] = defaultdict(list)

        # Build mapping of variable names to sections
        for section_key, section in self._sections.items():
            for var_name in section.variables:
                var_to_sections[var_name].append(section_key)

        # Find duplicates and format error
        duplicates = {
            var: sections
            for var, sections in var_to_sections.items()
            if len(sections) > 1
        }

        if duplicates:
            errors = [
                "Variable names must be unique across all sections, but found duplicates:"
            ]
            errors.extend(
                f"  - '{var}' appears in sections: {', '.join(secs)}"
                for var, secs in sorted(duplicates.items())
            )
            errors.append(
                "\nPlease rename variables to be unique or consolidate them into a single section."
            )
            error_msg = "\n".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _validate_section_toggle(self, section: VariableSection) -> None:
        """Validate that toggle variable is of type bool if it exists.

        If the toggle variable doesn't exist (e.g., filtered out), removes the toggle.

        Args:
            section: The section to validate

        Raises:
            ValueError: If toggle variable exists but is not boolean type
        """
        if not section.toggle:
            return

        toggle_var = section.variables.get(section.toggle)
        if not toggle_var:
            # Toggle variable doesn't exist (e.g., was filtered out) - remove toggle metadata
            section.toggle = None
            return

        if toggle_var.type != "bool":
            raise ValueError(
                f"Section '{section.key}' toggle variable '{section.toggle}' must be type 'bool', "
                f"but is type '{toggle_var.type}'"
            )

    @staticmethod
    def _parse_need(need_str: str) -> tuple[str, Optional[Any]]:
        """Parse a need string into variable name and expected value(s).

        Supports three formats:
        1. New format with multiple values: "variable_name=value1,value2" - checks if variable equals any value
        2. New format with single value: "variable_name=value" - checks if variable equals value
        3. Old format (backwards compatibility): "section_name" - checks if section is enabled

        Args:
            need_str: Need specification string

        Returns:
            Tuple of (variable_or_section_name, expected_value)
            For old format, expected_value is None (means check section enabled)
            For new format, expected_value is the string value(s) after '=' (string or list)

        Examples:
            "traefik_enabled=true" -> ("traefik_enabled", "true")
            "storage_mode=nfs" -> ("storage_mode", "nfs")
            "network_mode=bridge,macvlan" -> ("network_mode", ["bridge", "macvlan"])
            "traefik" -> ("traefik", None)  # Old format: section name
        """
        if "=" in need_str:
            # New format: variable=value or variable=value1,value2
            parts = need_str.split("=", 1)
            var_name = parts[0].strip()
            value_part = parts[1].strip()

            # Check if multiple values are provided (comma-separated)
            if "," in value_part:
                values = [v.strip() for v in value_part.split(",")]
                return (var_name, values)
            else:
                return (var_name, value_part)
        else:
            # Old format: section name (backwards compatibility)
            return (need_str.strip(), None)

    def _is_need_satisfied(self, need_str: str) -> bool:
        """Check if a single need condition is satisfied.

        Args:
            need_str: Need specification ("variable=value", "variable=value1,value2" or "section_name")

        Returns:
            True if need is satisfied, False otherwise
        """
        var_or_section, expected_value = self._parse_need(need_str)

        if expected_value is None:
            # Old format: check if section is enabled (backwards compatibility)
            section = self._sections.get(var_or_section)
            if not section:
                logger.warning(f"Need references missing section '{var_or_section}'")
                return False
            return section.is_enabled()
        else:
            # New format: check if variable has expected value(s)
            variable = self._variable_map.get(var_or_section)
            if not variable:
                logger.warning(f"Need references missing variable '{var_or_section}'")
                return False

            # Convert actual value for comparison
            try:
                actual_value = variable.convert(variable.value)

                # Handle multiple expected values (comma-separated in needs)
                if isinstance(expected_value, list):
                    # Check if actual value matches any of the expected values
                    for expected in expected_value:
                        expected_converted = variable.convert(expected)

                        # Handle boolean comparisons specially
                        if variable.type == "bool":
                            if bool(actual_value) == bool(expected_converted):
                                return True
                        else:
                            # String comparison for other types
                            if actual_value is not None and str(actual_value) == str(
                                expected_converted
                            ):
                                return True
                    return False  # None of the expected values matched
                else:
                    # Single expected value (original behavior)
                    expected_converted = variable.convert(expected_value)

                    # Handle boolean comparisons specially
                    if variable.type == "bool":
                        return bool(actual_value) == bool(expected_converted)

                    # String comparison for other types
                    return (
                        str(actual_value) == str(expected_converted)
                        if actual_value is not None
                        else False
                    )
            except Exception as e:
                logger.debug(f"Failed to compare need '{need_str}': {e}")
                return False

    def _validate_dependencies(self) -> None:
        """Validate section dependencies for cycles and missing references.

        Raises:
            ValueError: If circular dependencies or missing section references are found
        """
        # Check for missing dependencies in sections
        for section_key, section in self._sections.items():
            for dep in section.needs:
                var_or_section, expected_value = self._parse_need(dep)

                if expected_value is None:
                    # Old format: validate section exists
                    if var_or_section not in self._sections:
                        raise ValueError(
                            f"Section '{section_key}' depends on '{var_or_section}', but '{var_or_section}' does not exist"
                        )
                else:
                    # New format: validate variable exists
                    # NOTE: We only warn here, not raise an error, because the variable might be
                    # added later during merge with module spec. The actual runtime check in
                    # _is_need_satisfied() will handle missing variables gracefully.
                    if var_or_section not in self._variable_map:
                        logger.debug(
                            f"Section '{section_key}' has need '{dep}', but variable '{var_or_section}' "
                            f"not found (might be added during merge)"
                        )

        # Check for missing dependencies in variables
        for var_name, variable in self._variable_map.items():
            for dep in variable.needs:
                dep_var, expected_value = self._parse_need(dep)
                if expected_value is not None:  # Only validate new format
                    if dep_var not in self._variable_map:
                        # NOTE: We only warn here, not raise an error, because the variable might be
                        # added later during merge with module spec. The actual runtime check in
                        # _is_need_satisfied() will handle missing variables gracefully.
                        logger.debug(
                            f"Variable '{var_name}' has need '{dep}', but variable '{dep_var}' "
                            f"not found (might be added during merge)"
                        )

        # Check for circular dependencies using depth-first search
        # Note: Only checks section-level dependencies in old format (section names)
        # Variable-level dependencies (variable=value) don't create cycles in the same way
        visited = set()
        rec_stack = set()

        def has_cycle(section_key: str) -> bool:
            visited.add(section_key)
            rec_stack.add(section_key)

            section = self._sections[section_key]
            for dep in section.needs:
                # Only check circular deps for old format (section references)
                dep_name, expected_value = self._parse_need(dep)
                if expected_value is None and dep_name in self._sections:
                    # Old format section dependency - check for cycles
                    if dep_name not in visited:
                        if has_cycle(dep_name):
                            return True
                    elif dep_name in rec_stack:
                        raise ValueError(
                            f"Circular dependency detected: '{section_key}' depends on '{dep_name}', "
                            f"which creates a cycle"
                        )

            rec_stack.remove(section_key)
            return False

        for section_key in self._sections:
            if section_key not in visited:
                has_cycle(section_key)

    def is_section_satisfied(self, section_key: str) -> bool:
        """Check if all dependencies for a section are satisfied.

        Supports both formats:
        - Old format: "section_name" - checks if section is enabled (backwards compatible)
        - New format: "variable=value" - checks if variable has specific value

        Args:
            section_key: The key of the section to check

        Returns:
            True if all dependencies are satisfied, False otherwise
        """
        section = self._sections.get(section_key)
        if not section:
            return False

        # No dependencies = always satisfied
        if not section.needs:
            return True

        # Check each dependency using the unified need satisfaction logic
        for need in section.needs:
            if not self._is_need_satisfied(need):
                logger.debug(f"Section '{section_key}' need '{need}' is not satisfied")
                return False

        return True

    def is_variable_satisfied(self, var_name: str) -> bool:
        """Check if all dependencies for a variable are satisfied.

        A variable is satisfied if all its needs are met.
        Needs are specified as "variable_name=value".

        Args:
            var_name: The name of the variable to check

        Returns:
            True if all dependencies are satisfied, False otherwise
        """
        variable = self._variable_map.get(var_name)
        if not variable:
            return False

        # No dependencies = always satisfied
        if not variable.needs:
            return True

        # Check each dependency
        for need in variable.needs:
            if not self._is_need_satisfied(need):
                logger.debug(f"Variable '{var_name}' need '{need}' is not satisfied")
                return False

        return True

    def reset_disabled_bool_variables(self) -> list[str]:
        """Reset bool variables with unsatisfied dependencies to False.

        This ensures that disabled bool variables don't accidentally remain True
        and cause confusion in templates or configuration.

        Note: CLI-provided variables are NOT reset here - they are validated
        later in validate_all() to provide better error messages.

        Returns:
            List of variable names that were reset
        """
        reset_vars = []

        for section_key, section in self._sections.items():
            # Check if section dependencies are satisfied
            section_satisfied = self.is_section_satisfied(section_key)
            is_enabled = section.is_enabled()

            for var_name, variable in section.variables.items():
                # Only process bool variables
                if variable.type != "bool":
                    continue

                # Check if variable's own dependencies are satisfied
                var_satisfied = self.is_variable_satisfied(var_name)

                # If section is disabled OR variable dependencies aren't met, reset to False
                if not section_satisfied or not is_enabled or not var_satisfied:
                    # Only reset if current value is not already False
                    if variable.value is not False:
                        # Don't reset CLI-provided variables - they'll be validated later
                        if variable.origin == "cli":
                            continue

                        # Store original value if not already stored (for display purposes)
                        if not hasattr(variable, "_original_disabled"):
                            variable._original_disabled = variable.value

                        variable.value = False
                        reset_vars.append(var_name)
                        logger.debug(
                            f"Reset disabled bool variable '{var_name}' to False "
                            f"(section satisfied: {section_satisfied}, enabled: {is_enabled}, "
                            f"var satisfied: {var_satisfied})"
                        )

        return reset_vars

    def sort_sections(self) -> None:
        """Sort sections with the following priority:

        1. Dependencies come before dependents (topological sort)
        2. Required sections first (in their original order)
        3. Enabled sections with satisfied dependencies next (in their original order)
        4. Disabled sections or sections with unsatisfied dependencies last (in their original order)

        This maintains the original ordering within each group while organizing
        sections logically for display and user interaction, and ensures that
        sections are prompted in the correct dependency order.
        """
        # First, perform topological sort to respect dependencies
        sorted_keys = self._topological_sort()

        # Then apply priority sorting within dependency groups
        section_items = [(key, self._sections[key]) for key in sorted_keys]

        # Define sort key: (priority, original_index)
        # Priority: 0 = required, 1 = enabled with satisfied dependencies, 2 = disabled or unsatisfied dependencies
        def get_sort_key(item_with_index):
            index, (key, section) = item_with_index
            if section.required:
                priority = 0
            elif section.is_enabled() and self.is_section_satisfied(key):
                priority = 1
            else:
                priority = 2
            return (priority, index)

        # Sort with original index to maintain order within each priority group
        # Note: This preserves the topological order from earlier
        sorted_items = sorted(enumerate(section_items), key=get_sort_key)

        # Rebuild _sections dict in new order
        self._sections = {key: section for _, (key, section) in sorted_items}

        # NOTE: Sort variables within each section by their dependencies.
        # This is critical for correct behavior in both display and prompts:
        # 1. DISPLAY: Variables are shown in logical order (dependencies before dependents)
        # 2. PROMPTS: Users are asked for dependency values BEFORE dependent values
        #    Example: network_mode (bridge/host/macvlan) is prompted before
        #             network_macvlan_ipv4_address (which needs network_mode=macvlan)
        # 3. VALIDATION: Ensures config/CLI overrides can be checked in correct order
        # Without this sorting, users would be prompted for irrelevant variables or see
        # confusing variable order in the UI.
        for section in self._sections.values():
            section.sort_variables(self._is_need_satisfied)

    def _topological_sort(self) -> List[str]:
        """Perform topological sort on sections based on dependencies using Kahn's algorithm."""
        in_degree = {key: len(section.needs) for key, section in self._sections.items()}
        queue = [key for key, degree in in_degree.items() if degree == 0]
        queue.sort(
            key=lambda k: list(self._sections.keys()).index(k)
        )  # Preserve original order
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # Update in-degree for dependent sections
            for key, section in self._sections.items():
                if current in section.needs:
                    in_degree[key] -= 1
                    if in_degree[key] == 0:
                        queue.append(key)

        # Fallback to original order if cycle detected
        if len(result) != len(self._sections):
            logger.warning("Topological sort incomplete - using original order")
            return list(self._sections.keys())

        return result

    def get_sections(self) -> Dict[str, VariableSection]:
        """Get all sections in the collection."""
        return self._sections.copy()

    def get_section(self, key: str) -> Optional[VariableSection]:
        """Get a specific section by its key."""
        return self._sections.get(key)

    def has_sections(self) -> bool:
        """Check if the collection has any sections."""
        return bool(self._sections)

    def get_all_values(self) -> dict[str, Any]:
        """Get all variable values as a dictionary."""
        # NOTE: Uses _variable_map for O(1) access
        return {
            name: var.convert(var.value) for name, var in self._variable_map.items()
        }

    def get_satisfied_values(self) -> dict[str, Any]:
        """Get variable values only from sections with satisfied dependencies.

        This respects both toggle states and section dependencies, ensuring that:
        - Variables from disabled sections (toggle=false) are excluded EXCEPT required variables
        - Variables from sections with unsatisfied dependencies are excluded
        - Required variables are always included if their section dependencies are satisfied

        Returns:
            Dictionary of variable names to values for satisfied sections only
        """
        satisfied_values = {}

        for section_key, section in self._sections.items():
            # Skip sections with unsatisfied dependencies (even required variables need satisfied deps)
            if not self.is_section_satisfied(section_key):
                logger.debug(
                    f"Excluding variables from section '{section_key}' - dependencies not satisfied"
                )
                continue

            # Check if section is enabled
            is_enabled = section.is_enabled()

            if is_enabled:
                # Include all variables from enabled section
                for var_name, variable in section.variables.items():
                    satisfied_values[var_name] = variable.convert(variable.value)
            else:
                # Section is disabled - only include required variables
                logger.debug(
                    f"Section '{section_key}' is disabled - including only required variables"
                )
                for var_name, variable in section.variables.items():
                    if variable.required:
                        logger.debug(
                            f"Including required variable '{var_name}' from disabled section '{section_key}'"
                        )
                        satisfied_values[var_name] = variable.convert(variable.value)

        return satisfied_values

    def get_sensitive_variables(self) -> Dict[str, Any]:
        """Get only the sensitive variables with their values."""
        return {
            name: var.value
            for name, var in self._variable_map.items()
            if var.sensitive and var.value
        }

    def apply_defaults(
        self, defaults: dict[str, Any], origin: str = "cli"
    ) -> list[str]:
        """Apply default values to variables, updating their origin.

        Args:
            defaults: Dictionary mapping variable names to their default values
            origin: Source of these defaults (e.g., 'config', 'cli')

        Returns:
            List of variable names that were successfully updated
        """
        # NOTE: This method uses the _variable_map for a significant performance gain,
        # as it allows direct O(1) lookup of variables instead of iterating
        # through all sections to find a match.
        successful = []
        errors = []

        for var_name, value in defaults.items():
            try:
                variable = self._variable_map.get(var_name)
                if not variable:
                    logger.warning(f"Variable '{var_name}' not found in template")
                    continue

                # Check if this is a toggle variable for a required section
                # If trying to set it to false, warn and skip
                for section in self._sections.values():
                    if (
                        section.required
                        and section.toggle
                        and section.toggle == var_name
                    ):
                        # Convert value to bool to check if it's false
                        try:
                            bool_value = variable.convert(value)
                            if not bool_value:
                                logger.warning(
                                    f"Ignoring attempt to disable toggle '{var_name}' for required section '{section.key}' via {origin}"
                                )
                                continue
                        except Exception:
                            pass  # If conversion fails, let normal validation handle it

                # Check if variable's needs are satisfied
                # If not, warn that the override will have no effect
                if not self.is_variable_satisfied(var_name):
                    # Build a friendly message about which needs aren't satisfied
                    unmet_needs = []
                    for need in variable.needs:
                        if not self._is_need_satisfied(need):
                            unmet_needs.append(need)
                    needs_str = ", ".join(unmet_needs) if unmet_needs else "unknown"
                    logger.warning(
                        f"Setting '{var_name}' via {origin} will have no effect - needs not satisfied: {needs_str}"
                    )
                    # Continue anyway to store the value (it might become relevant later)

                # Store original value before overriding (for display purposes)
                # Only store if this is the first time config is being applied
                if origin == "config" and not hasattr(variable, "_original_stored"):
                    variable.original_value = variable.value
                    variable._original_stored = True

                # Convert and set the new value
                converted_value = variable.convert(value)
                variable.value = converted_value

                # Set origin to the current source (not a chain)
                variable.origin = origin

                successful.append(var_name)

            except ValueError as e:
                error_msg = f"Invalid value for '{var_name}': {value} - {e}"
                errors.append(error_msg)
                logger.error(error_msg)

        if errors:
            logger.warning(f"Some defaults failed to apply: {'; '.join(errors)}")

        return successful

    def validate_all(self) -> None:
        """Validate all variables in the collection.

        Validates:
        - All variables in enabled sections with satisfied dependencies
        - Required variables even if their section is disabled (but dependencies must be satisfied)
        - CLI-provided bool variables with unsatisfied dependencies
        """
        errors: list[str] = []

        # First, check for CLI-provided bool variables with unsatisfied dependencies
        for section_key, section in self._sections.items():
            section_satisfied = self.is_section_satisfied(section_key)
            is_enabled = section.is_enabled()

            for var_name, variable in section.variables.items():
                # Check CLI-provided bool variables with unsatisfied dependencies
                if (
                    variable.type == "bool"
                    and variable.origin == "cli"
                    and variable.value is not False
                ):
                    var_satisfied = self.is_variable_satisfied(var_name)

                    if not section_satisfied or not is_enabled or not var_satisfied:
                        # Build error message with unmet needs (use set to avoid duplicates)
                        unmet_needs = set()
                        if not section_satisfied:
                            for need in section.needs:
                                if not self._is_need_satisfied(need):
                                    unmet_needs.add(need)
                        if not var_satisfied:
                            for need in variable.needs:
                                if not self._is_need_satisfied(need):
                                    unmet_needs.add(need)

                        needs_str = (
                            ", ".join(sorted(unmet_needs))
                            if unmet_needs
                            else "dependencies not satisfied"
                        )
                        errors.append(
                            f"{section.key}.{var_name} (set via CLI to {variable.value} but requires: {needs_str})"
                        )

        # Then validate all other variables
        for section_key, section in self._sections.items():
            # Skip sections with unsatisfied dependencies (even for required variables)
            if not self.is_section_satisfied(section_key):
                logger.debug(
                    f"Skipping validation for section '{section_key}' - dependencies not satisfied"
                )
                continue

            # Check if section is enabled
            is_enabled = section.is_enabled()

            if not is_enabled:
                logger.debug(
                    f"Section '{section_key}' is disabled - validating only required variables"
                )

            # Validate variables in the section
            for var_name, variable in section.variables.items():
                # Skip all variables (including required ones) in disabled sections
                # Required variables are only required when their section is actually enabled
                if not is_enabled:
                    continue

                try:
                    # Skip autogenerated variables when empty
                    if variable.autogenerated and not variable.value:
                        continue

                    # Check required fields
                    if variable.value is None:
                        # Optional variables can be None/empty
                        if hasattr(variable, "optional") and variable.optional:
                            continue
                        if variable.is_required():
                            errors.append(
                                f"{section.key}.{var_name} (required - no default provided)"
                            )
                        continue

                    # Validate typed value
                    typed = variable.convert(variable.value)
                    if variable.type not in ("bool",) and not typed:
                        msg = f"{section.key}.{var_name}"
                        errors.append(
                            f"{msg} (required - cannot be empty)"
                            if variable.is_required()
                            else f"{msg} (empty)"
                        )

                except ValueError as e:
                    errors.append(f"{section.key}.{var_name} (invalid format: {e})")

        if errors:
            error_msg = "Variable validation failed: " + ", ".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

    def merge(
        self,
        other_spec: Union[Dict[str, Any], "VariableCollection"],
        origin: str = "override",
    ) -> "VariableCollection":
        """Merge another spec or VariableCollection into this one with precedence tracking.

        OPTIMIZED: Works directly on objects without dict conversions for better performance.

        The other spec/collection has higher precedence and will override values in self.
        Creates a new VariableCollection with merged data.

        Args:
            other_spec: Either a spec dictionary or another VariableCollection to merge
            origin: Origin label for variables from other_spec (e.g., 'template', 'config')

        Returns:
            New VariableCollection with merged data

        Example:
            module_vars = VariableCollection(module_spec)
            template_vars = module_vars.merge(template_spec, origin='template')
            # Variables from template_spec override module_spec
            # Origins tracked: 'module' or 'module -> template'
        """
        # Convert dict to VariableCollection if needed (only once)
        if isinstance(other_spec, dict):
            other = VariableCollection(other_spec)
        else:
            other = other_spec

        # Create new collection without calling __init__ (optimization)
        merged = VariableCollection.__new__(VariableCollection)
        merged._sections = {}
        merged._variable_map = {}

        # First pass: clone sections from self
        for section_key, self_section in self._sections.items():
            if section_key in other._sections:
                # Section exists in both - will merge
                merged._sections[section_key] = self._merge_sections(
                    self_section, other._sections[section_key], origin
                )
            else:
                # Section only in self - clone it
                merged._sections[section_key] = self_section.clone()

        # Second pass: add sections that only exist in other
        for section_key, other_section in other._sections.items():
            if section_key not in merged._sections:
                # New section from other - clone with origin update
                merged._sections[section_key] = other_section.clone(
                    origin_update=origin
                )

        # Rebuild variable map for O(1) lookups
        for section in merged._sections.values():
            for var_name, variable in section.variables.items():
                merged._variable_map[var_name] = variable

        # Validate dependencies after merge is complete
        merged._validate_dependencies()

        return merged

    def _merge_sections(
        self, self_section: VariableSection, other_section: VariableSection, origin: str
    ) -> VariableSection:
        """Merge two sections, with other_section taking precedence."""
        merged_section = self_section.clone()

        # Update section metadata from other (other takes precedence)
        # Explicit null/empty values clear the property (reset mechanism)
        for attr in ("title", "description", "toggle"):
            if (
                hasattr(other_section, "_explicit_fields")
                and attr in other_section._explicit_fields
            ):
                # Set to the other value even if null/empty (enables explicit reset)
                setattr(merged_section, attr, getattr(other_section, attr))

        merged_section.required = other_section.required
        # Respect explicit clears for dependencies (explicit null/empty clears, missing field preserves)
        if (
            hasattr(other_section, "_explicit_fields")
            and "needs" in other_section._explicit_fields
        ):
            merged_section.needs = (
                other_section.needs.copy() if other_section.needs else []
            )

        # Merge variables
        for var_name, other_var in other_section.variables.items():
            if var_name in merged_section.variables:
                # Variable exists in both - merge with other taking precedence
                self_var = merged_section.variables[var_name]

                # Build update dict with ONLY explicitly provided fields from other
                update = {"origin": origin}
                field_map = {
                    "type": other_var.type,
                    "description": other_var.description,
                    "prompt": other_var.prompt,
                    "options": other_var.options,
                    "sensitive": other_var.sensitive,
                    "extra": other_var.extra,
                }

                # Add fields that were explicitly provided, even if falsy/empty
                for field, value in field_map.items():
                    if field in other_var._explicit_fields:
                        update[field] = value

                # For boolean flags, only copy if explicitly provided in other
                # This prevents False defaults from overriding True values
                for bool_field in ("optional", "autogenerated", "required"):
                    if bool_field in other_var._explicit_fields:
                        update[bool_field] = getattr(other_var, bool_field)

                # Special handling for needs (allow explicit null/empty to clear)
                if "needs" in other_var._explicit_fields:
                    update["needs"] = other_var.needs.copy() if other_var.needs else []

                # Special handling for value/default (allow explicit null to clear)
                if "value" in other_var._explicit_fields:
                    update["value"] = other_var.value
                elif "default" in other_var._explicit_fields:
                    update["value"] = other_var.value

                merged_section.variables[var_name] = self_var.clone(update=update)
            else:
                # New variable from other - clone with origin
                merged_section.variables[var_name] = other_var.clone(
                    update={"origin": origin}
                )

        return merged_section

    def filter_to_used(
        self, used_variables: Set[str], keep_sensitive: bool = True
    ) -> "VariableCollection":
        """Filter collection to only variables that are used (or sensitive).

        OPTIMIZED: Works directly on objects without dict conversions for better performance.

        Creates a new VariableCollection containing only the variables in used_variables.
        Sections with no remaining variables are removed.

        Args:
            used_variables: Set of variable names that are actually used
            keep_sensitive: If True, also keep sensitive variables even if not in used set

        Returns:
            New VariableCollection with filtered variables

        Example:
            all_vars = VariableCollection(spec)
            used_vars = all_vars.filter_to_used({'var1', 'var2', 'var3'})
            # Only var1, var2, var3 (and any sensitive vars) remain
        """
        # Create new collection without calling __init__ (optimization)
        filtered = VariableCollection.__new__(VariableCollection)
        filtered._sections = {}
        filtered._variable_map = {}

        # Filter each section
        for section_key, section in self._sections.items():
            # Create a new section with same metadata
            filtered_section = VariableSection(
                {
                    "key": section.key,
                    "title": section.title,
                    "description": section.description,
                    "toggle": section.toggle,
                    "required": section.required,
                    "needs": section.needs.copy() if section.needs else None,
                }
            )

            # Clone only the variables that should be included
            for var_name, variable in section.variables.items():
                # Include if used OR if sensitive (and keep_sensitive is True)
                should_include = var_name in used_variables or (
                    keep_sensitive and variable.sensitive
                )

                if should_include:
                    filtered_section.variables[var_name] = variable.clone()

            # Only add section if it has variables
            if filtered_section.variables:
                filtered._sections[section_key] = filtered_section
                # Add variables to map
                for var_name, variable in filtered_section.variables.items():
                    filtered._variable_map[var_name] = variable

        return filtered

    def get_all_variable_names(self) -> Set[str]:
        """Get set of all variable names across all sections.

        Returns:
            Set of all variable names
        """
        return set(self._variable_map.keys())
