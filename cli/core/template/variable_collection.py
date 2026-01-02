from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from .variable import Variable
from .variable_section import VariableSection

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

        self._sections: dict[str, VariableSection] = {}
        # NOTE: The _variable_map provides a flat, O(1) lookup for any variable by its name,
        # avoiding the need to iterate through sections. It stores references to the same
        # Variable objects contained in the _set structure.
        self._variable_map: dict[str, Variable] = {}
        self._initialize_sections(spec)
        # Validate dependencies after all sections are loaded
        self._validate_dependencies()

    @classmethod
    def from_json(cls, json_spec: list[dict[str, Any]]) -> VariableCollection:
        """Create VariableCollection from JSON array format.

        Args:
            json_spec: List of section specifications in JSON format.
                      Expected format:
                      [
                        {
                          "key": "section_key",
                          "title": "Section Title",
                          "description": "Optional description",
                          "toggle": "optional_toggle_var_name",
                          "required": true,
                          "needs": "dependency_section",
                          "vars": [
                            {
                              "name": "var_name",
                              "description": "Variable description",
                              "type": "str",
                              "default": "default_value",
                              ...
                            }
                          ]
                        }
                      ]

        Returns:
            VariableCollection initialized from JSON spec

        Raises:
            ValueError: If json_spec is not a list or has invalid structure
        """
        if not isinstance(json_spec, list):
            raise ValueError("JSON spec must be a list")

        # Convert JSON array format to dict format expected by __init__
        dict_spec = {}
        for section_data in json_spec:
            section_key = cls._validate_and_extract_section_key(section_data)
            section_dict = cls._build_section_dict(section_data)
            vars_dict = cls._convert_vars_to_dict(section_data, section_key)
            section_dict["vars"] = vars_dict
            dict_spec[section_key] = section_dict

        # Create and return VariableCollection using standard __init__
        return cls(dict_spec)

    @staticmethod
    def _validate_and_extract_section_key(section_data: Any) -> str:
        """Validate section data and extract the section key.

        Args:
            section_data: Section data to validate

        Returns:
            The section key

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(section_data, dict):
            raise ValueError(f"Section must be a dict, got {type(section_data).__name__}")

        if "key" not in section_data:
            raise ValueError("Section missing required 'key' field")

        if "vars" not in section_data:
            raise ValueError(f"Section '{section_data['key']}' missing required 'vars' field")

        return section_data["key"]

    @staticmethod
    def _build_section_dict(section_data: dict[str, Any]) -> dict[str, Any]:
        """Build section dictionary with optional fields.

        Args:
            section_data: Source section data

        Returns:
            Dictionary with only present optional fields
        """
        section_dict = {}
        optional_fields = ["title", "description", "toggle", "needs"]

        for field in optional_fields:
            if field in section_data:
                section_dict[field] = section_data[field]

        return section_dict

    @staticmethod
    def _convert_vars_to_dict(section_data: dict[str, Any], section_key: str) -> dict[str, Any]:
        """Convert vars array to dictionary format.

        Args:
            section_data: Section data containing vars array
            section_key: Section key for error messages

        Returns:
            Dictionary mapping variable names to their specifications

        Raises:
            ValueError: If vars format is invalid
        """
        if not isinstance(section_data["vars"], list):
            raise ValueError(f"Section '{section_key}' vars must be a list")

        vars_dict = {}
        for var_data in section_data["vars"]:
            if not isinstance(var_data, dict):
                raise ValueError(f"Variable in section '{section_key}' must be a dict")

            if "name" not in var_data:
                raise ValueError(f"Variable in section '{section_key}' missing 'name' field")

            var_name = var_data["name"]
            # Copy all fields except 'name' to the var dict
            var_dict = {k: v for k, v in var_data.items() if k != "name"}
            vars_dict[var_name] = var_dict

        return vars_dict

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
        if "needs" in data:
            section_init_data["needs"] = data["needs"]

        return VariableSection(section_init_data)

    def _initialize_variables(self, section: VariableSection, vars_data: dict[str, Any]) -> None:
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
        var_to_sections: dict[str, list[str]] = defaultdict(list)

        # Build mapping of variable names to sections
        for section_key, section in self._sections.items():
            for var_name in section.variables:
                var_to_sections[var_name].append(section_key)

        # Find duplicates and format error
        duplicates = {var: sections for var, sections in var_to_sections.items() if len(sections) > 1}

        if duplicates:
            errors = ["Variable names must be unique across all sections, but found duplicates:"]
            errors.extend(
                f"  - '{var}' appears in sections: {', '.join(secs)}" for var, secs in sorted(duplicates.items())
            )
            errors.append("\nPlease rename variables to be unique or consolidate them into a single section.")
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
    def _parse_need(need_str: str) -> tuple[str, bool, Any | None]:
        """Parse a need string into variable name, operator, and expected value(s).

        Supports four formats:
        1. Negation with multiple values: "variable_name!=value1,value2" - checks if variable does NOT equal any value
        2. Negation with single value: "variable_name!=value" - checks if variable does NOT equal value
        3. Equality with multiple values: "variable_name=value1,value2" - checks if variable equals any value
        4. Equality with single value: "variable_name=value" - checks if variable equals value
        5. Old format (backwards compatibility): "section_name" - checks if section is enabled

        Args:
            need_str: Need specification string

        Returns:
            Tuple of (variable_or_section_name, is_positive, expected_value)
            - is_positive: True for '=' (must match), False for '!=' (must NOT match)
            - For old format, expected_value is None (means check section enabled) and is_positive is True
            - For new format, expected_value is the string value(s) after operator (string or list)

        Examples:
            "traefik_enabled=true" -> ("traefik_enabled", True, "true")
            "storage_mode=nfs" -> ("storage_mode", True, "nfs")
            "network_mode=bridge,macvlan" -> ("network_mode", True, ["bridge", "macvlan"])
            "network_mode!=host,macvlan" -> ("network_mode", False, ["host", "macvlan"])
            "network_mode!=host" -> ("network_mode", False, "host")
            "traefik" -> ("traefik", True, None)  # Old format: section name
        """
        # Check for != operator first (must check before = to avoid false positive)
        if "!=" in need_str:
            # Negation format: variable!=value or variable!=value1,value2
            parts = need_str.split("!=", 1)
            var_name = parts[0].strip()
            value_part = parts[1].strip()

            # Check if multiple values are provided (comma-separated)
            if "," in value_part:
                values = [v.strip() for v in value_part.split(",")]
                return (var_name, False, values)
            return (var_name, False, value_part)

        if "=" in need_str:
            # Equality format: variable=value or variable=value1,value2
            parts = need_str.split("=", 1)
            var_name = parts[0].strip()
            value_part = parts[1].strip()

            # Check if multiple values are provided (comma-separated)
            if "," in value_part:
                values = [v.strip() for v in value_part.split(",")]
                return (var_name, True, values)
            return (var_name, True, value_part)

        # Old format: section name (backwards compatibility)
        return (need_str.strip(), True, None)

    def _is_need_satisfied(self, need_str: str) -> bool:
        """Check if a single need condition is satisfied.

        Args:
            need_str: Need specification ("variable=value", "variable!=value",
                     "variable=value1,value2" or "section_name")

        Returns:
            True if need is satisfied, False otherwise
        """
        var_or_section, is_positive, expected_value = self._parse_need(need_str)

        # Old format: check if section is enabled (backwards compatibility)
        if expected_value is None:
            result = self._check_section_need(var_or_section)
            section = self._sections.get(var_or_section)
            if section:
                logger.debug(
                    f"Checking section need '{need_str}': "
                    f"exists=True, enabled={section.is_enabled()}, satisfied={result}"
                )
            else:
                logger.debug(f"Checking section need '{need_str}': exists=False, satisfied={result}")
            return result

        # New format: check if variable has expected value(s)
        result = self._check_variable_need(var_or_section, is_positive, expected_value, need_str)
        variable = self._variable_map.get(var_or_section)
        if variable:
            operator = "=" if is_positive else "!="
            logger.debug(
                f"Checking variable need '{need_str}': "
                f"var_value={variable.value} {operator} expected={expected_value}, satisfied={result}"
            )
        else:
            logger.debug(f"Checking variable need '{need_str}': variable not found, satisfied={result}")
        return result

    def _check_section_need(self, section_name: str) -> bool:
        """Check if a section-based need is satisfied."""
        section = self._sections.get(section_name)
        if not section:
            logger.warning(f"Need references missing section '{section_name}'")
            return False
        return section.is_enabled()

    def _check_variable_need(self, var_name: str, is_positive: bool, expected_value: Any, need_str: str) -> bool:
        """Check if a variable-based need is satisfied.

        Args:
            var_name: Variable name to check
            is_positive: True for '=' (must match), False for '!=' (must NOT match)
            expected_value: Expected value(s) to compare against
            need_str: Original need string for logging

        Returns:
            True if need is satisfied, False otherwise
        """
        variable = self._variable_map.get(var_name)
        if not variable:
            # Variable doesn't exist - ignore the constraint and treat as satisfied
            # This allows templates to override sections without breaking needs constraints
            logger.debug(
                f"Need '{need_str}' references missing variable '{var_name}' - "
                f"ignoring constraint and treating as satisfied"
            )
            return True

        try:
            actual_value = variable.convert(variable.value)

            # Handle multiple expected values
            if isinstance(expected_value, list):
                matches = self._matches_any_value(variable, actual_value, expected_value)
            else:
                # Single expected value
                matches = self._matches_single_value(variable, actual_value, expected_value)

            # For positive checks (=), return match result directly
            # For negative checks (!=), invert the result
            return matches if is_positive else not matches
        except Exception as e:
            logger.debug(f"Failed to compare need '{need_str}': {e}")
            return False

    def _matches_any_value(self, variable: Variable, actual_value: Any, expected_values: list) -> bool:
        """Check if actual value matches any of the expected values."""
        for expected in expected_values:
            expected_converted = variable.convert(expected)
            if self._values_match(variable, actual_value, expected_converted):
                return True
        return False

    def _matches_single_value(self, variable: Variable, actual_value: Any, expected_value: Any) -> bool:
        """Check if actual value matches the expected value."""
        expected_converted = variable.convert(expected_value)
        return self._values_match(variable, actual_value, expected_converted)

    def _values_match(self, variable: Variable, actual: Any, expected: Any) -> bool:
        """Compare two values based on variable type."""
        if variable.type == "bool":
            return bool(actual) == bool(expected)
        return actual is not None and str(actual) == str(expected)

    def _validate_dependencies(self) -> None:
        """Validate section dependencies for cycles.

        Missing section references are logged as warnings but do not raise errors,
        allowing templates to be modified without breaking when dependencies are removed.

        Raises:
            ValueError: If circular dependencies are found
        """
        # Check for missing dependencies in sections
        for section_key, section in self._sections.items():
            for dep in section.needs:
                var_or_section, _is_positive, expected_value = self._parse_need(dep)

                if expected_value is None:
                    # Old format: validate section exists
                    if var_or_section not in self._sections:
                        logger.warning(
                            f"Section '{section_key}' depends on '{var_or_section}', "
                            f"but '{var_or_section}' does not exist. Ignoring this dependency."
                        )
                # New format: validate variable exists
                # NOTE: We only warn here, not raise an error, because the variable might be
                # added later during merge with module spec. The actual runtime check in
                # _is_need_satisfied() will handle missing variables gracefully.
                elif var_or_section not in self._variable_map:
                    logger.debug(
                        f"Section '{section_key}' has need '{dep}', but variable '{var_or_section}' "
                        f"not found (might be added during merge)"
                    )

        # Check for missing dependencies in variables
        for var_name, variable in self._variable_map.items():
            for dep in variable.needs:
                dep_var, _is_positive, expected_value = self._parse_need(dep)
                # Only validate new format and check if variable is missing
                if expected_value is not None and dep_var not in self._variable_map:
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
                dep_name, _is_positive, expected_value = self._parse_need(dep)
                # Old format section dependency - check for cycles
                if expected_value is None and dep_name in self._sections:
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
        logger.debug("Starting reset of disabled bool variables")

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
                if (
                    (not section_satisfied or not is_enabled or not var_satisfied)
                    and variable.value is not False
                    and variable.origin != "cli"
                ):
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

        if reset_vars:
            logger.debug(f"Reset {len(reset_vars)} disabled bool variables: {', '.join(reset_vars)}")
        else:
            logger.debug("No bool variables needed reset")

        return reset_vars

    def sort_sections(self) -> None:
        """Sort sections with the following priority:

        1. Dependencies come before dependents (topological sort)
        2. Enabled sections with satisfied dependencies first (in their original order)
        3. Disabled sections or sections with unsatisfied dependencies last (in their original order)

        This maintains the original ordering within each group while organizing
        sections logically for display and user interaction, and ensures that
        sections are prompted in the correct dependency order.
        """
        # First, perform topological sort to respect dependencies
        sorted_keys = self._topological_sort()

        # Then apply priority sorting within dependency groups
        section_items = [(key, self._sections[key]) for key in sorted_keys]

        # Define sort key: (priority, original_index)
        # Priority: 0 = enabled with satisfied dependencies, 1 = disabled or unsatisfied dependencies
        def get_sort_key(item_with_index):
            index, (key, section) = item_with_index
            priority = 0 if section.is_enabled() and self.is_section_satisfied(key) else 1
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

    def _topological_sort(self) -> list[str]:
        """Perform topological sort on sections based on dependencies using Kahn's algorithm."""
        in_degree = {key: len(section.needs) for key, section in self._sections.items()}
        queue = [key for key, degree in in_degree.items() if degree == 0]
        queue.sort(key=lambda k: list(self._sections.keys()).index(k))  # Preserve original order
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
            missing = set(self._sections.keys()) - set(result)
            # Identify which sections have circular dependencies
            circular_deps = []
            for section_key in missing:
                section = self._sections[section_key]
                if section.needs:
                    circular_deps.append(f"{section_key} (needs: {', '.join(section.needs)})")

            logger.warning(
                f"Topological sort incomplete - circular dependency detected. "
                f"Missing sections: {', '.join(missing)}. "
                f"Circular dependencies: {'; '.join(circular_deps) if circular_deps else 'none identified'}. "
                f"Using original order."
            )
            return list(self._sections.keys())

        return result

    def get_sections(self) -> dict[str, VariableSection]:
        """Get all sections in the collection."""
        return self._sections.copy()

    def get_section(self, key: str) -> VariableSection | None:
        """Get a specific section by its key."""
        return self._sections.get(key)

    def has_sections(self) -> bool:
        """Check if the collection has any sections."""
        return bool(self._sections)

    def get_all_values(self) -> dict[str, Any]:
        """Get all variable values as a dictionary."""
        # NOTE: Uses _variable_map for O(1) access
        return {name: var.convert(var.value) for name, var in self._variable_map.items()}

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
                logger.debug(f"Excluding variables from section '{section_key}' - dependencies not satisfied")
                continue

            # Check if section is enabled
            is_enabled = section.is_enabled()

            if is_enabled:
                # Include all variables from enabled section
                for var_name, variable in section.variables.items():
                    satisfied_values[var_name] = variable.convert(variable.value)
            else:
                # Section is disabled - exclude all variables
                logger.debug(f"Section '{section_key}' is disabled - excluding all variables")

        return satisfied_values

    def get_sensitive_variables(self) -> dict[str, Any]:
        """Get only the sensitive variables with their values."""
        return {name: var.value for name, var in self._variable_map.items() if var.sensitive and var.value}

    def apply_defaults(self, defaults: dict[str, Any], origin: str = "cli") -> list[str]:
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
                    logger.debug(
                        f"Default value for '{var_name}' not applicable to this template (variable not defined)"
                    )
                    continue

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
            # Raise exception to halt execution on validation errors
            raise ValueError(f"Variable validation failed: {'; '.join(errors)}")

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
        self._validate_cli_bool_variables(errors)

        # Then validate all other variables
        self._validate_section_variables(errors)

        if errors:
            error_msg = "Variable validation failed: " + ", ".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _validate_cli_bool_variables(self, errors: list[str]) -> None:
        """Validate CLI-provided bool variables with unsatisfied dependencies."""
        for section_key, section in self._sections.items():
            section_satisfied = self.is_section_satisfied(section_key)
            is_enabled = section.is_enabled()

            for var_name, variable in section.variables.items():
                # Check CLI-provided bool variables with unsatisfied dependencies
                if not self._is_cli_bool_variable(variable):
                    continue

                var_satisfied = self.is_variable_satisfied(var_name)
                if section_satisfied and is_enabled and var_satisfied:
                    continue

                # Build error message with unmet needs
                unmet_needs = self._collect_unmet_needs(section, variable, section_satisfied, var_satisfied)
                needs_str = ", ".join(sorted(unmet_needs)) if unmet_needs else "dependencies not satisfied"
                errors.append(f"{section.key}.{var_name} (set via CLI to {variable.value} but requires: {needs_str})")

    def _is_cli_bool_variable(self, variable: Variable) -> bool:
        """Check if variable is a CLI-provided boolean."""
        return variable.type == "bool" and variable.origin == "cli" and variable.value is not False

    def _collect_unmet_needs(
        self, section, variable: Variable, section_satisfied: bool, var_satisfied: bool
    ) -> set[str]:
        """Collect all unmet needs from section and variable."""
        unmet_needs = set()
        if not section_satisfied:
            for need in section.needs:
                if not self._is_need_satisfied(need):
                    unmet_needs.add(need)
        if not var_satisfied:
            for need in variable.needs:
                if not self._is_need_satisfied(need):
                    unmet_needs.add(need)
        return unmet_needs

    def _validate_section_variables(self, errors: list[str]) -> None:
        """Validate all variables in each section."""
        for section_key, section in self._sections.items():
            # Skip sections with unsatisfied dependencies
            if not self.is_section_satisfied(section_key):
                logger.debug(f"Skipping validation for section '{section_key}' - dependencies not satisfied")
                continue

            # Check if section is enabled
            is_enabled = section.is_enabled()
            if not is_enabled:
                logger.debug(f"Section '{section_key}' is disabled - skipping all variables")
                continue

            # Validate variables in the section
            for var_name, variable in section.variables.items():
                self._validate_single_variable(section, var_name, variable, errors)

    def _validate_single_variable(self, section, var_name: str, variable: Variable, errors: list[str]) -> None:
        """Validate a single variable and append errors."""
        try:
            # Skip autogenerated variables when empty
            if variable.autogenerated and not variable.value:
                return

            # Skip variables with unsatisfied needs (even if required)
            if not self.is_variable_satisfied(var_name):
                logger.debug(f"Skipping validation for variable '{var_name}' - needs not satisfied")
                return

            # Check required fields
            if variable.value is None:
                if variable.is_required():
                    # Enhanced error message with context
                    origin_info = f" from {variable.origin}" if variable.origin else ""
                    logger.debug(
                        f"Required variable validation failed: '{var_name}'{origin_info} "
                        f"in section '{section.key}' has no value and no default"
                    )
                    errors.append(f"{section.key}.{var_name} (required{origin_info} - no default provided)")
                return
            typed = variable.convert(variable.value)
            if variable.type not in ("bool",) and not typed:
                msg = f"{section.key}.{var_name}"
                error = f"{msg} (required - cannot be empty)" if variable.is_required() else f"{msg} (empty)"
                errors.append(error)

        except ValueError as e:
            errors.append(f"{section.key}.{var_name} (invalid format: {e})")

    def merge(
        self,
        other_spec: dict[str, Any] | VariableCollection,
        origin: str = "override",
    ) -> VariableCollection:
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
        logger.debug(f"Starting merge operation with origin '{origin}'")

        # Convert dict to VariableCollection if needed (only once)
        other = VariableCollection(other_spec) if isinstance(other_spec, dict) else other_spec

        # Create new collection without calling __init__ (optimization)
        merged = VariableCollection.__new__(VariableCollection)
        merged._sections = {}
        merged._variable_map = {}

        # First pass: clone sections from self
        for section_key, self_section in self._sections.items():
            if section_key in other._sections:
                # Section exists in both - will merge
                merged._sections[section_key] = self._merge_sections(self_section, other._sections[section_key], origin)
            else:
                # Section only in self - clone it
                merged._sections[section_key] = self_section.clone()

        # Second pass: add sections that only exist in other
        for section_key, other_section in other._sections.items():
            if section_key not in merged._sections:
                # New section from other - clone with origin update
                merged._sections[section_key] = other_section.clone(origin_update=origin)

        # Rebuild variable map for O(1) lookups
        for section in merged._sections.values():
            for var_name, variable in section.variables.items():
                merged._variable_map[var_name] = variable

        # Log merge statistics
        self_var_count = sum(len(s.variables) for s in self._sections.values())
        other_var_count = sum(len(s.variables) for s in other._sections.values())
        merged_var_count = len(merged._variable_map)
        logger.debug(
            f"Merge complete: {len(self._sections)} sections (base) + {len(other._sections)} sections (override) = "
            f"{len(merged._sections)} sections, {self_var_count} vars + "
            f"{other_var_count} vars = {merged_var_count} vars"
        )

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
            if hasattr(other_section, "_explicit_fields") and attr in other_section._explicit_fields:
                # Set to the other value even if null/empty (enables explicit reset)
                setattr(merged_section, attr, getattr(other_section, attr))

        # Respect explicit clears for dependencies (explicit null/empty clears, missing field preserves)
        if hasattr(other_section, "_explicit_fields") and "needs" in other_section._explicit_fields:
            merged_section.needs = other_section.needs.copy() if other_section.needs else []

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
                for bool_field in ("autogenerated", "required"):
                    if bool_field in other_var._explicit_fields:
                        update[bool_field] = getattr(other_var, bool_field)

                # Special handling for needs (allow explicit null/empty to clear)
                if "needs" in other_var._explicit_fields:
                    update["needs"] = other_var.needs.copy() if other_var.needs else []

                # Special handling for value/default (allow explicit null to clear)
                if "value" in other_var._explicit_fields or "default" in other_var._explicit_fields:
                    update["value"] = other_var.value

                merged_section.variables[var_name] = self_var.clone(update=update)
            else:
                # New variable from other - clone with origin
                merged_section.variables[var_name] = other_var.clone(update={"origin": origin})

        return merged_section

    def filter_to_used(self, used_variables: set[str], keep_sensitive: bool = True) -> VariableCollection:
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
                    "needs": section.needs.copy() if section.needs else None,
                }
            )

            # Clone only the variables that should be included
            for var_name, variable in section.variables.items():
                # Include if used OR if sensitive (and keep_sensitive is True)
                should_include = var_name in used_variables or (keep_sensitive and variable.sensitive)

                if should_include:
                    filtered_section.variables[var_name] = variable.clone()

            # Only add section if it has variables
            if filtered_section.variables:
                filtered._sections[section_key] = filtered_section
                # Add variables to map
                for var_name, variable in filtered_section.variables.items():
                    filtered._variable_map[var_name] = variable

        return filtered

    def get_all_variable_names(self) -> set[str]:
        """Get set of all variable names across all sections.

        Returns:
            Set of all variable names
        """
        return set(self._variable_map.keys())
