"""Build dependency-aware template validation cases."""

from __future__ import annotations

import itertools
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cli.core.template import Template
    from cli.core.template.variable import Variable
    from cli.core.template.variable_collection import VariableCollection


@dataclass(frozen=True)
class MatrixOptions:
    """Options controlling dependency matrix generation."""

    max_combinations: int = 100


@dataclass(frozen=True)
class DependencyCondition:
    """Structured representation of a needs condition."""

    variable: str
    positive: bool
    values: tuple[str, ...] | None = None


@dataclass
class ValidationCase:
    """A named variable configuration to render and validate."""

    name: str
    variables: VariableCollection
    overrides: dict[str, Any]


class DependencyMatrixBuilder:
    """Create practical dependency-aware validation cases for one template."""

    def __init__(self, template: Template, options: MatrixOptions | None = None) -> None:
        self.template = template
        self.options = options or MatrixOptions()
        self.base_variables = template.variables
        self._conditions = self._collect_conditions()

    def build(self) -> list[ValidationCase]:
        """Build named, satisfiable, deduplicated validation cases."""
        variable_values = self._build_branch_value_sets()
        raw_cases = self._build_raw_cases(variable_values)
        return self._materialize_cases(raw_cases)

    def _collect_conditions(self) -> list[DependencyCondition]:
        conditions: list[DependencyCondition] = []

        for section in self.base_variables.get_sections().values():
            conditions.extend(self._parse_conditions(section.needs))
            for variable in section.variables.values():
                conditions.extend(self._parse_conditions(variable.needs))

        return conditions

    def _parse_conditions(self, needs: list[str]) -> list[DependencyCondition]:
        conditions = []
        for need in needs:
            condition = self._parse_condition(need)
            if condition is not None:
                conditions.append(condition)
        return conditions

    @staticmethod
    def _parse_condition(need: str) -> DependencyCondition | None:
        if "!=" in need:
            variable, raw_values = need.split("!=", 1)
            return DependencyCondition(variable.strip(), False, DependencyMatrixBuilder._split_values(raw_values))

        if "=" in need:
            variable, raw_values = need.split("=", 1)
            return DependencyCondition(variable.strip(), True, DependencyMatrixBuilder._split_values(raw_values))

        return None

    @staticmethod
    def _split_values(raw_values: str) -> tuple[str, ...]:
        return tuple(value.strip() for value in raw_values.split(",") if value.strip())

    def _build_branch_value_sets(self) -> dict[str, list[Any]]:
        value_sets: dict[str, list[Any]] = {}
        variables = self.base_variables._variable_map

        # Bool variables are cheap and often control template branches directly.
        for name, variable in variables.items():
            if variable.type == "bool":
                value_sets[name] = [False, True]

        # Section toggles may not follow a naming convention, so include them explicitly.
        for section in self.base_variables.get_sections().values():
            if section.toggle and section.toggle in variables:
                value_sets[section.toggle] = [False, True]

        for condition in self._conditions:
            variable = variables.get(condition.variable)
            if variable is None:
                continue

            values = self._condition_values(variable, condition)
            if not values:
                continue

            current_values = value_sets.setdefault(condition.variable, [])
            for value in values:
                if value not in current_values:
                    current_values.append(value)

        return {name: values for name, values in value_sets.items() if values}

    def _condition_values(self, variable: Variable, condition: DependencyCondition) -> list[Any]:
        values: list[Any] = []

        if variable.type == "bool":
            return [False, True]

        if variable.type == "enum":
            values.extend(self._matching_enum_values(variable, condition))
            if variable.value is not None and variable.value not in values:
                values.append(variable.value)
            return values

        if condition.values:
            values.extend(condition.values)
        if variable.value is not None and variable.value not in values:
            values.append(variable.value)
        return values

    @staticmethod
    def _matching_enum_values(variable: Variable, condition: DependencyCondition) -> list[str]:
        options = list(variable.options or [])
        if not condition.values:
            return options

        if condition.positive:
            return [value for value in condition.values if value in options]

        excluded = set(condition.values)
        return [value for value in options if value not in excluded]

    def _build_raw_cases(self, value_sets: dict[str, list[Any]]) -> list[tuple[str, dict[str, Any]]]:
        if not value_sets:
            return [("defaults", {})]

        count = 1
        for values in value_sets.values():
            count *= len(values)

        if count <= self.options.max_combinations:
            return self._cartesian_cases(value_sets)

        return self._reduced_cases(value_sets)

    def _cartesian_cases(self, value_sets: dict[str, list[Any]]) -> list[tuple[str, dict[str, Any]]]:
        names = sorted(value_sets)
        cases: list[tuple[str, dict[str, Any]]] = [("defaults", {})]

        for index, values in enumerate(itertools.product(*(value_sets[name] for name in names)), start=1):
            overrides = dict(zip(names, values, strict=True))
            cases.append((self._case_name(f"matrix-{index}", overrides), overrides))

        return cases

    def _reduced_cases(self, value_sets: dict[str, list[Any]]) -> list[tuple[str, dict[str, Any]]]:
        cases: list[tuple[str, dict[str, Any]]] = [("defaults", {})]

        bool_names = sorted(name for name in value_sets if self.base_variables._variable_map.get(name).type == "bool")
        if bool_names:
            cases.append(("all-bools-false", dict.fromkeys(bool_names, False)))
            cases.append(("all-bools-true", dict.fromkeys(bool_names, True)))

        for name in sorted(value_sets):
            for value in value_sets[name]:
                overrides = {name: value}
                cases.append((self._case_name("branch", overrides), overrides))

        return cases

    def _materialize_cases(self, raw_cases: list[tuple[str, dict[str, Any]]]) -> list[ValidationCase]:
        cases: list[ValidationCase] = []
        seen_effective_states: set[str] = set()

        for name, overrides in raw_cases:
            variables = self._fresh_variables()
            if overrides:
                variables.apply_defaults(overrides, origin="matrix")
            variables.reset_disabled_bool_variables()

            state_key = self._state_key(variables.get_satisfied_values())
            if state_key in seen_effective_states:
                continue
            seen_effective_states.add(state_key)
            cases.append(ValidationCase(name=name, variables=variables, overrides=overrides))

        return cases

    def _fresh_variables(self) -> VariableCollection:
        return self.base_variables.merge({}, origin="matrix")

    @staticmethod
    def _state_key(values: dict[str, Any]) -> str:
        return json.dumps(values, sort_keys=True, default=str)

    @staticmethod
    def _case_name(prefix: str, overrides: dict[str, Any]) -> str:
        details = ", ".join(f"{key}={value}" for key, value in sorted(overrides.items()))
        return f"{prefix}: {details}" if details else prefix
