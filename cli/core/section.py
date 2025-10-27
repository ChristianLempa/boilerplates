from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, List, Optional

from .variable import Variable


class VariableSection:
    """Groups variables together with shared metadata for presentation."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize VariableSection from a dictionary.

        Args:
            data: Dictionary containing section specification with required 'key' and 'title' keys
        """
        if not isinstance(data, dict):
            raise ValueError("VariableSection data must be a dictionary")

        if "key" not in data:
            raise ValueError("VariableSection data must contain 'key'")

        if "title" not in data:
            raise ValueError("VariableSection data must contain 'title'")

        self.key: str = data["key"]
        self.title: str = data["title"]
        self.variables: OrderedDict[str, Variable] = OrderedDict()
        self.description: Optional[str] = data.get("description")
        self.toggle: Optional[str] = data.get("toggle")
        # Track which fields were explicitly provided (to support explicit clears)
        self._explicit_fields: set[str] = set(data.keys())
        # Default "general" section to required=True, all others to required=False
        self.required: bool = data.get("required", data["key"] == "general")
        # Section dependencies - can be string or list of strings
        # Supports semicolon-separated multiple conditions: "var1=value1;var2=value2,value3"
        needs_value = data.get("needs")
        if needs_value:
            if isinstance(needs_value, str):
                # Split by semicolon to support multiple AND conditions in a single string
                # Example: "traefik_enabled=true;network_mode=bridge,macvlan"
                self.needs: List[str] = [
                    need.strip() for need in needs_value.split(";") if need.strip()
                ]
            elif isinstance(needs_value, list):
                self.needs: List[str] = needs_value
            else:
                raise ValueError(
                    f"Section '{self.key}' has invalid 'needs' value: must be string or list"
                )
        else:
            self.needs: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        """Serialize VariableSection to a dictionary for storage."""
        section_dict = {
            "required": self.required,
            "vars": {name: var.to_dict() for name, var in self.variables.items()},
        }

        # Add optional fields if present
        for field in ("title", "description", "toggle"):
            if value := getattr(self, field):
                section_dict[field] = value

        # Store dependencies (single value if only one, list otherwise)
        if self.needs:
            section_dict["needs"] = (
                self.needs[0] if len(self.needs) == 1 else self.needs
            )

        return section_dict

    def is_enabled(self) -> bool:
        """Check if section is currently enabled based on toggle variable.

        Returns:
            True if section is enabled (required, no toggle, or toggle is True), False otherwise
        """
        # Required sections are always enabled, regardless of toggle
        if self.required:
            return True

        if not self.toggle:
            return True

        toggle_var = self.variables.get(self.toggle)
        if not toggle_var:
            return True

        try:
            return bool(toggle_var.convert(toggle_var.value))
        except Exception:
            return False

    def clone(self, origin_update: Optional[str] = None) -> "VariableSection":
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
                "required": self.required,
                "needs": self.needs.copy() if self.needs else None,
            }
        )

        # Deep copy all variables
        for var_name, variable in self.variables.items():
            if origin_update:
                cloned.variables[var_name] = variable.clone(
                    update={"origin": origin_update}
                )
            else:
                cloned.variables[var_name] = variable.clone()

        return cloned

    def sort_variables(self, is_need_satisfied_func=None) -> None:
        """Sort variables within section for optimal display and user interaction.

        Current sorting strategy:
        - Variables with no dependencies come first
        - Variables that depend on others come after their dependencies (topological sort)
        - Original order is preserved for variables at the same dependency level

        Future sorting strategies can be added here (e.g., by type, required first, etc.)

        Args:
            is_need_satisfied_func: Optional function to check if a variable need is satisfied
                                   (reserved for future use in conditional sorting)
        """
        if not self.variables:
            return

        # Build dependency graph
        var_list = list(self.variables.keys())
        var_set = set(var_list)

        # For each variable, find which OTHER variables in THIS section it depends on
        dependencies = {var_name: [] for var_name in var_list}
        for var_name in var_list:
            variable = self.variables[var_name]
            if variable.needs:
                for need in variable.needs:
                    # Parse need format: "variable_name=value"
                    dep_var = need.split("=")[0] if "=" in need else need
                    # Only track dependencies within THIS section
                    if dep_var in var_set and dep_var != var_name:
                        dependencies[var_name].append(dep_var)

        # Topological sort using Kahn's algorithm
        in_degree = {var_name: len(deps) for var_name, deps in dependencies.items()}
        queue = [var for var, degree in in_degree.items() if degree == 0]
        # Preserve original order for variables with same dependency level
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
            for var_name in var_list:
                if var_name not in result:
                    result.append(var_name)

        # Rebuild variables OrderedDict in new order
        sorted_vars = OrderedDict()
        for var_name in result:
            sorted_vars[var_name] = self.variables[var_name]
        self.variables = sorted_vars
