"""
Core variables support for interactive collection and detection.

Provides a BaseVariables class that can detect which variable sets are used
in a Jinja2 template and interactively collect values from the user.
"""
from typing import Dict, List, Tuple, Set, Any
import jinja2
from jinja2 import meta
import typer
from .prompt import PromptHandler


class BaseVariables:
    """Base implementation for variable sets and interactive prompting.

     Subclasses should set `variable_sets` to one of two shapes:

     1) Legacy shape (mapping of set-name -> { var_name: { ... } })
         { "general": { "foo": { ... }, ... } }

     2) New shape (mapping of set-name -> { "prompt": str, "variables": { var_name: { ... } } })
         { "general": { "prompt": "...", "variables": { "foo": { ... } } } }
    """

    variable_sets: Dict[str, Dict[str, Any]] = {}

    def __init__(self) -> None:
        # Flattened list of all declared variable names -> (set_name, meta)
        self._declared: Dict[str, Tuple[str, Dict[str, Any]]] = {}
        # Support both legacy and new shapes. If the set value contains a
        # 'variables' key, use that mapping; otherwise assume the mapping is
        # directly the vars map (legacy).
        for set_name, set_def in getattr(self, "variable_sets", {}).items():
            vars_map = set_def.get("variables") if isinstance(set_def, dict) and "variables" in set_def else set_def
            if not isinstance(vars_map, dict):
                continue
            for var_name, meta_info in vars_map.items():
                self._declared[var_name] = (set_name, meta_info)

    def find_used_variables(self, template_content: str) -> Set[str]:
        """Parse the Jinja2 template and return the set of variable names used."""
        env = jinja2.Environment()
        try:
            ast = env.parse(template_content)
            used = meta.find_undeclared_variables(ast)
            return set(used)
        except Exception:
            # If parsing fails, fallback to an empty set (safe behavior)
            return set()

    def find_used_subscript_keys(self, template_content: str) -> Dict[str, Set[str]]:
        """Return mapping of variable name -> set of string keys accessed via subscripting

        Example: for template using service_port['http'] and service_port['https']
        this returns { 'service_port': {'http', 'https'} }.
        """
        try:
            env = jinja2.Environment()
            ast = env.parse(template_content)
            # Walk AST and collect Subscript nodes
            from jinja2 import nodes

            subs: Dict[str, Set[str]] = {}

            for node in ast.find_all(nodes.Getitem):
                # Getitem node structure: node.node (value), node.arg (index)
                try:
                    if isinstance(node.node, nodes.Name):
                        var_name = node.node.name
                        # index can be Const (string) or Name/other; handle Const
                        idx = node.arg
                        if isinstance(idx, nodes.Const) and isinstance(idx.value, str):
                            subs.setdefault(var_name, set()).add(idx.value)
                except Exception:
                    continue

            return subs
        except Exception:
            return {}

    def extract_template_defaults(self, template_content: str) -> Dict[str, Any]:
        """Extract default values from Jinja2 expressions like {{ var | default(value) }}."""
        import re

        def _parse_literal(s: str):
            s = s.strip()
            if s.startswith("'") and s.endswith("'"):
                return s[1:-1]
            if s.startswith('"') and s.endswith('"'):
                return s[1:-1]
            if s.isdigit():
                return int(s)
            return s

        defaults: Dict[str, Any] = {}


        # Match {{ var['key'] | default(value) }} and {{ var | default(value) }}
        pattern_subscript = r'\{\{\s*(\w+)\s*\[\s*["\']([^"\']+)["\']\s*\]\s*\|\s*default\(([^)]+)\)\s*\}\}'
        for var, key, default_str in re.findall(pattern_subscript, template_content):
            if var not in defaults or not isinstance(defaults[var], dict):
                defaults[var] = {}
            defaults[var][key] = _parse_literal(default_str)

        pattern_scalar = r'\{\{\s*(\w+)\s*\|\s*default\(([^)]+)\)\s*\}\}'
        for var, default_str in re.findall(pattern_scalar, template_content):
            # Only set scalar default if not already set as a dict
            if var not in defaults:
                defaults[var] = _parse_literal(default_str)

        # Handle simple {% set name = other | default('val') %} patterns
        set_pattern = r"\{%\s*set\s+(\w+)\s*=\s*([^%]+?)\s*%}"
        for set_var, expr in re.findall(set_pattern, template_content):
            m = re.match(r"(\w+)\s*\|\s*default\(([^)]+)\)", expr.strip())
            if m:
                src_var, src_default = m.groups()
                if src_var in defaults:
                    defaults[set_var] = defaults[src_var]
                else:
                    defaults[set_var] = _parse_literal(src_default)

        # Resolve transitive references: if a default is an identifier that
        # points to another default, follow it; if it points to a declared
        # variable with a metadata default, use that.
        def _resolve_ref(value, seen: Set[str]):
            if not isinstance(value, str):
                return value
            if value in seen:
                return value
            seen.add(value)
            if value in defaults:
                return _resolve_ref(defaults[value], seen)
            if value in self._declared:
                declared_def = self._declared[value][1].get("default")
                if declared_def is not None:
                    return declared_def
            return value

        for k in list(defaults.keys()):
            defaults[k] = _resolve_ref(defaults[k], set([k]))

        return defaults

    def determine_variable_sets(self, template_content: str) -> Tuple[List[str], Set[str]]:
        """Return a list of variable set names that contain any used variables.

        Also returns the raw set of used variable names.
        """
        used = self.find_used_variables(template_content)
        matched_sets: List[str] = []
        for set_name, set_def in getattr(self, "variable_sets", {}).items():
            vars_map = set_def.get("variables") if isinstance(set_def, dict) and "variables" in set_def else set_def
            if not isinstance(vars_map, dict):
                continue
            if any(var in used for var in vars_map.keys()):
                matched_sets.append(set_name)
        return matched_sets, used

    def collect_values(self, used_vars: Set[str], template_defaults: Dict[str, Any] = None, used_subscripts: Dict[str, Set[str]] = None) -> Dict[str, Any]:
        """Interactively prompt for values for the variables that appear in the template.

        For variables that were declared in `variable_sets` we use their metadata.
        For unknown variables, we fall back to a generic prompt.
        """
        prompt_handler = PromptHandler(self._declared, getattr(self, "variable_sets", {}))
        return prompt_handler.collect_values(used_vars, template_defaults, used_subscripts)
