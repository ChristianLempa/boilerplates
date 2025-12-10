from __future__ import annotations

from collections import OrderedDict
from typing import Any

from ..exceptions import VariableError
from .variable import Variable


class VariableSection:
    """Groups variables together with shared metadata for presentation."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize VariableSection from a dictionary.

        Args:
            data: Dictionary containing section specification with required 'key' and 'title' keys
        """
        if not isinstance(data, dict):
            raise VariableError("VariableSection data must be a dictionary")

        if "key" not in data:
            raise VariableError("VariableSection data must contain 'key'")

        if "title" not in data:
            raise VariableError("VariableSection data must contain 'title'")

        self.key: str = data["key"]
        self.title: str = data["title"]
        self.variables: OrderedDict[str, Variable] = OrderedDict()
        self.description: str | None = data.get("description")
        self.toggle: str | None = data.get("toggle")
        # Track which fields were explicitly provided (to support explicit clears)
        self._explicit_fields: set[str] = set(data.keys())
        # Section dependencies - can be string or list of strings
        # Supports semicolon-separated multiple conditions: "var1=value1;var2=value2,value3"
        needs_value = data.get("needs")
        if needs_value:
            if isinstance(needs_value, str):
                # Split by semicolon to support multiple AND conditions in a single string
                # Example: "traefik_enabled=true;network_mode=bridge,macvlan"
                self.needs: list[str] = [need.strip() for need in needs_value.split(";") if need.strip()]
            elif isinstance(needs_value, list):
                self.needs: list[str] = needs_value
            else:
                raise VariableError(f"Section '{self.key}' has invalid 'needs' value: must be string or list")
        else:
            self.needs: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        """Serialize VariableSection to a dictionary for storage."""
        section_dict = {
            "vars": {name: var.to_dict() for name, var in self.variables.items()},
        }

        # Add optional fields if present
        for field in ("title", "description", "toggle"):
            if value := getattr(self, field):
                section_dict[field] = value

        # Store dependencies (single value if only one, list otherwise)
        if self.needs:
            section_dict["needs"] = self.needs[0] if len(self.needs) == 1 else self.needs

        return section_dict

    def is_enabled(self) -> bool:
        """Check if section is currently enabled based on toggle variable.

        Returns:
            True if section is enabled (no toggle, or toggle is True), False otherwise
        """
        if not self.toggle:
            return True

        toggle_var = self.variables.get(self.toggle)
        if not toggle_var:
            return True

        try:
            return bool(toggle_var.convert(toggle_var.value))
        except Exception:
            return False

    def clone(self, origin_update: str | None = None) -> VariableSection:
        """Create a deep copy of the section with all variables.

        This is more efficient than converting to dict and back when copying sections.

        Args:
            origin_update: Optional origin string to apply to all cloned variables

        Returns:
            New VariableSection instance with deep-copied variables

        Example:
            section2 = section1.clone(origin_update='template')
        """
        # Create new section with same metadata
        cloned = VariableSection(
            {
                "key": self.key,
                "title": self.title,
                "description": self.description,
                "toggle": self.toggle,
                "needs": self.needs.copy() if self.needs else None,
            }
        )

        # Deep copy all variables
        for var_name, variable in self.variables.items():
            if origin_update:
                cloned.variables[var_name] = variable.clone(update={"origin": origin_update})
            else:
                cloned.variables[var_name] = variable.clone()

        return cloned

    def _build_dependency_graph(self, var_list: list[str]) -> dict[str, list[str]]:
        """Build dependency graph for variables in this section."""
        var_set = set(var_list)
        dependencies = {var_name: [] for var_name in var_list}

        for var_name in var_list:
            variable = self.variables[var_name]
            if not variable.needs:
                continue

            for need in variable.needs:
                # Parse need format: "variable_name=value"
                dep_var = need.split("=")[0] if "=" in need else need
                # Only track dependencies within THIS section
                if dep_var in var_set and dep_var != var_name:
                    dependencies[var_name].append(dep_var)

        return dependencies

    def _topological_sort(self, var_list: list[str], dependencies: dict[str, list[str]]) -> list[str]:
        """Perform topological sort using Kahn's algorithm."""
        in_degree = {var_name: len(deps) for var_name, deps in dependencies.items()}
        queue = [var for var, degree in in_degree.items() if degree == 0]
        queue.sort(key=lambda v: var_list.index(v))
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # Update in-degree for dependent variables
            for var_name, deps in dependencies.items():
                if current in deps:
                    in_degree[var_name] -= 1
                    if in_degree[var_name] == 0:
                        queue.append(var_name)
                        queue.sort(key=lambda v: var_list.index(v))

        # If not all variables were sorted (cycle), append remaining in original order
        if len(result) != len(var_list):
            result.extend(var_name for var_name in var_list if var_name not in result)

        return result

    def sort_variables(self, _is_need_satisfied_func=None) -> None:
        """Sort variables within section for optimal display and user interaction.

        Current sorting strategy:
        - Variables with no dependencies come first
        - Variables that depend on others come after their dependencies (topological sort)
        - Original order is preserved for variables at the same dependency level

        Future sorting strategies can be added here (e.g., by type, required first, etc.)

        Args:
            _is_need_satisfied_func: Optional function to check if a variable need is satisfied
                                    (unused, reserved for future use in conditional sorting)
        """
        if not self.variables:
            return

        var_list = list(self.variables.keys())
        dependencies = self._build_dependency_graph(var_list)
        result = self._topological_sort(var_list, dependencies)

        # Rebuild variables OrderedDict in new order
        self.variables = OrderedDict((var_name, self.variables[var_name]) for var_name in result)
