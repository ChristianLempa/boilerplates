from typing import Any, Dict, Optional, List, Set, Tuple
from rich.prompt import Prompt, IntPrompt, Confirm
import typer
import sys

class PromptHandler:
    def __init__(self, declared_variables: Dict[str, Tuple[str, Dict[str, Any]]], variable_sets: Dict[str, Dict[str, Any]]):
        self._declared = declared_variables
        self.variable_sets = variable_sets

    @staticmethod
    def ask_bool(prompt_text: str, default: bool = False, description: Optional[str] = None) -> bool:
        """Ask a yes/no question, render default in cyan when in a TTY, and
        fall back to typer.confirm when not attached to a TTY.
        """
        if description and description.strip():
            typer.secho(description, fg=typer.colors.BRIGHT_BLACK)
            
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            return typer.confirm(prompt_text, default=default)

        if default:
            indicator = "[cyan]Y[/cyan]/n"
        else:
            indicator = "y/[cyan]N[/cyan]"

        prompt_full = f"{prompt_text} [{indicator}]"
        resp = Prompt.ask(prompt_full, default="", show_default=False)
        if resp is None or str(resp).strip() == "":
            return bool(default)
        r = str(resp).strip().lower()
        return r[0] in ("y", "1", "t")

    @staticmethod
    def ask_int(prompt_text: str, default: Optional[int] = None, description: Optional[str] = None) -> int:
        if description and description.strip():
            typer.secho(description, fg=typer.colors.BRIGHT_BLACK)
        return IntPrompt.ask(prompt_text, default=default, show_default=True)

    @staticmethod
    def ask_str(prompt_text: str, default: Optional[str] = None, show_default: bool = True, description: Optional[str] = None) -> str:
        if description and description.strip():
            typer.secho(description, fg=typer.colors.BRIGHT_BLACK)
        return Prompt.ask(prompt_text, default=default, show_default=show_default)

    def collect_values(self, used_vars: Set[str], template_defaults: Dict[str, Any] = None, used_subscripts: Dict[str, Set[str]] = None) -> Dict[str, Any]:
        """Interactively prompt for values for the variables that appear in the template.

        For variables that were declared in `variable_sets` we use their metadata.
        For unknown variables, we fall back to a generic prompt.
        """
        if template_defaults is None:
            template_defaults = {}
        values: Dict[str, Any] = {}

        # Group used vars by their set.
        # Iterate through declared variable_sets so the prompt order
        # matches the order variables were defined in each set.
        set_used_vars: Dict[str, List[str]] = {}
        for set_name, set_def in self.variable_sets.items():
            vars_map = set_def.get("variables") if isinstance(set_def, dict) and "variables" in set_def else set_def
            if not isinstance(vars_map, dict):
                continue
            for var_name in vars_map.keys():
                if var_name in used_vars and var_name in self._declared:
                    if set_name not in set_used_vars:
                        set_used_vars[set_name] = []
                    set_used_vars[set_name].append(var_name)
            
            # If the set name is used as a variable, include the set for prompting
            if set_name in used_vars and set_name not in set_used_vars:
                set_used_vars[set_name] = []

        # Process each set
        for set_name, vars_in_set in set_used_vars.items():
            # Retrieve per-set definition to pick up the custom prompt if provided
            set_def = self.variable_sets.get(set_name, {})
            set_prompt = set_def.get("prompt") if isinstance(set_def, dict) else None
            typer.secho(f"\n{set_name.title()} Settings", fg=typer.colors.BLUE, bold=True)

            def _print_defaults_for_set(vars_list):
                # Collect variables that have an effective default to print.
                printable = []
                for v in vars_list:
                    meta_info = self._declared[v][1]
                    display_name = meta_info.get("display_name", v.replace("_", " ").title())
                    default = self._get_effective_default(v, template_defaults, values)
                    # Skip variables that have no effective default (they must be provided by the user)
                    if default is None:
                        continue
                    printable.append((v, display_name, default))

                # If there are no defaults to show, don't print a header or blank line.
                if not printable:
                    return

                # Print a blank line and a consistent header for defaults so it matches
                # the 'Required ... Variables' section formatting.
                typer.secho("\nDefault %s Variables" % set_name.title(), fg=typer.colors.GREEN, bold=True)

                for v, display_name, default in printable:
                    # If variable is accessed with subscripts, show '(multiple)'
                    if used_subscripts and v in used_subscripts and used_subscripts[v]:
                        typer.secho(f"{display_name}: ", fg=typer.colors.BRIGHT_BLACK, nl=False)
                        typer.secho("(multiple)", fg=typer.colors.CYAN)
                    else:
                        typer.secho(f"{display_name}: ", fg=typer.colors.BRIGHT_BLACK, nl=False)
                        typer.secho(f"{default}", fg=typer.colors.CYAN)

            # Decide whether this set is enabled and whether it should be
            # customized. Support three modes in the set definition:
            # - 'always': True => the set is enabled and we skip the enable
            #    question (but may still ask to customize values)
            # - 'prompt_enable': str => ask this question first to enable the
            #    set (stores values[set_name] boolean)
            # - 'prompt' (existing): when provided, ask whether to customize
            #    the values. We ask 'prompt_enable' first when present, then
            #    'prompt' to decide whether to customize.

            set_always = bool(set_def.get('always', False))
            set_prompt_enable = set_def.get('prompt_enable')
            set_customize_prompt = set_prompt or f"Do you want to change the {set_name.title()} settings?"

            if set_always:
                enable_set = True
            elif set_prompt_enable:
                enable_set = self.ask_bool(set_prompt_enable, default=False)
            else:
                # No explicit enable prompt: fall back to asking the customize prompt
                # and treat that as enabling when answered Yes.
                enable_set = None

            # If we have a definitive enable decision, store it into values
            if enable_set is not None:
                values[set_name] = enable_set
                # If a declared variable exists with the same name, don't prompt it
                if set_name in vars_in_set:
                    vars_in_set = [v for v in vars_in_set if v != set_name]

            # If we didn't ask prompt_enable, ask the customize prompt directly
            if enable_set is None:
                # Check for undefined variables first, before asking if they want to enable
                undefined_vars_in_set = []
                for var in vars_in_set:
                    effective_default = self._get_effective_default(var, template_defaults, values)
                    if effective_default is None:
                        undefined_vars_in_set.append(var)
                
                # If there are undefined variables, we must enable this set
                if undefined_vars_in_set:
                    typer.secho(f"\n{set_name.title()} Settings", fg=typer.colors.BLUE, bold=True)
                    typer.secho(f"Required {set_name.title()} Variables", fg=typer.colors.YELLOW, bold=True)
                    for var in undefined_vars_in_set:
                        meta_info = self._declared[var][1]
                        display_name = meta_info.get("display_name", var.replace("_", " ").title())
                        vtype = meta_info.get("type", "str")
                        prompt = meta_info.get("prompt", f"Enter {display_name}")
                        description = meta_info.get("description")
                        
                        # Handle subscripted variables
                        subs = used_subscripts.get(var, set()) if used_subscripts else set()
                        if subs:
                            result_map = {}
                            for k in subs:
                                # Required sub-key: enforce non-empty
                                kval = Prompt.ask(f"Value for {display_name}['{k}']:", default="", show_default=False)
                                if not (sys.stdin.isatty() and sys.stdout.isatty()):
                                    # Non-interactive: empty value is an error
                                    if kval is None or str(kval).strip() == "":
                                        typer.secho(f"[red]Required value for {display_name}['{k}'] cannot be blank in non-interactive mode.[/red]")
                                        raise typer.Exit(code=1)
                                else:
                                    # Interactive: re-prompt until non-empty
                                    while kval is None or str(kval).strip() == "":
                                        typer.secho("Value cannot be blank. Please enter a value.", fg=typer.colors.YELLOW)
                                        kval = Prompt.ask(f"Value for {display_name}['{k}']:", default="", show_default=False)
                                result_map[k] = self._guess_and_cast(kval)
                            values[var] = result_map
                            continue

                        if vtype == "bool":
                            val = self.ask_bool(prompt, default=False, description=description)
                        elif vtype == "int":
                            val = self.ask_int(prompt, default=None, description=description)
                        else:
                            val = self.ask_str(prompt, default=None, show_default=False, description=description)
                        
                        values[var] = self._cast_value_from_input(val, vtype)
                    
                    # Since we prompted for required variables, enable the set
                    values[set_name] = True
                    if set_name in vars_in_set:
                        vars_in_set = [v for v in vars_in_set if v != set_name]
                    
                    # Print defaults and ask if they want to change others
                    _print_defaults_for_set(vars_in_set)
                    change_set = self.ask_bool(set_customize_prompt, default=False)
                    if not change_set:
                        # Use defaults for remaining variables
                        for var in vars_in_set:
                            if var not in values:  # Don't override variables we already prompted for
                                meta_info = self._declared[var][1]
                                default = self._get_effective_default(var, template_defaults, values)
                                values[var] = default
                        continue
                else:
                    # No undefined variables, ask the customize prompt as normal
                    change_set = self.ask_bool(set_customize_prompt, default=False)
                    values[set_name] = change_set
                    if set_name in vars_in_set:
                        vars_in_set = [v for v in vars_in_set if v != set_name]
                    if not change_set:
                        # Use defaults for this set
                        for var in vars_in_set:
                            if var not in values:  # Don't override variables that might have been set
                                meta_info = self._declared[var][1]
                                default = self._get_effective_default(var, template_defaults, values)
                                values[var] = default
                        continue

            # If we had an enable_set (True/False) and it is False, skip customizing
            if enable_set is not None and not enable_set:
                for var in vars_in_set:
                    if var not in values:  # Don't override variables that might have been set
                        meta_info = self._declared[var][1]
                        default = self._get_effective_default(var, template_defaults, values)
                        values[var] = default
                continue

            # At this point the set is enabled. Check for undefined variables first.
            undefined_vars_in_set = []
            for var in vars_in_set:
                effective_default = self._get_effective_default(var, template_defaults, values)
                if effective_default is None:
                    undefined_vars_in_set.append(var)
            
            # Prompt for undefined variables in this set
            if undefined_vars_in_set:
                typer.secho(f"\nRequired {set_name.title()} Variables", fg=typer.colors.YELLOW, bold=True)
                for var in undefined_vars_in_set:
                    meta_info = self._declared[var][1]
                    display_name = meta_info.get("display_name", var.replace("_", " ").title())
                    vtype = meta_info.get("type", "str")
                    prompt = meta_info.get("prompt", f"Enter {display_name}")
                    description = meta_info.get("description")
                    
                    # Handle subscripted variables
                    subs = used_subscripts.get(var, set()) if used_subscripts else set()
                    if subs:
                        result_map = {}
                        for k in subs:
                            # Required sub-key: enforce non-empty
                            kval = Prompt.ask(f"Value for {display_name}['{k}']:", default="", show_default=False)
                            if not (sys.stdin.isatty() and sys.stdout.isatty()):
                                if kval is None or str(kval).strip() == "":
                                    typer.secho(f"[red]Required value for {display_name}['{k}'] cannot be blank in non-interactive mode.[/red]")
                                    raise typer.Exit(code=1)
                            else:
                                while kval is None or str(kval).strip() == "":
                                    typer.secho("Value cannot be blank. Please enter a value.", fg=typer.colors.YELLOW)
                                    kval = Prompt.ask(f"Value for {display_name}['{k}']:", default="", show_default=False)
                            result_map[k] = self._guess_and_cast(kval)
                        values[var] = result_map
                        continue

                    if vtype == "bool":
                        val = self.ask_bool(prompt, default=False, description=description)
                    elif vtype == "int":
                        val = self.ask_int(prompt, default=None, description=description)
                    else:
                        val = self.ask_str(prompt, default=None, show_default=False, description=description)
                        # Enforce non-empty for required scalar variables
                        if not (sys.stdin.isatty() and sys.stdout.isatty()):
                            if val is None or str(val).strip() == "":
                                typer.secho(f"[red]Required value for {display_name} cannot be blank in non-interactive mode.[/red]")
                                raise typer.Exit(code=1)
                        else:
                            while val is None or str(val).strip() == "":
                                typer.secho("Value cannot be blank. Please enter a value.", fg=typer.colors.YELLOW)
                                val = self.ask_str(prompt, default=None, show_default=False, description=description)

                    values[var] = self._cast_value_from_input(val, vtype)

            # Print defaults now (only after enabling and prompting for required vars)
            # so the user sees current values before customizing.
            _print_defaults_for_set(vars_in_set)

            # If we have asked prompt_enable earlier (and the set is enabled),
            # now ask whether to customize. For 'always' sets we still ask the
            # customize prompt.
            if set_prompt_enable or set_always:
                change_set = self.ask_bool(set_customize_prompt, default=False)
                if not change_set:
                    for var in vars_in_set:
                        if var not in values:  # Don't override variables that might have been set
                            meta_info = self._declared[var][1]
                            default = self._get_effective_default(var, template_defaults, values)
                            values[var] = default
                    continue

            # Prompt for each variable in the set
            for var in vars_in_set:
                # Skip variables that have already been prompted for
                if var in values:
                    continue
                    
                meta_info = self._declared[var][1]
                display_name = meta_info.get("display_name", var.replace("_", " ").title())
                vtype = meta_info.get("type", "str")
                prompt = meta_info.get("prompt", f"Enter {display_name}")
                description = meta_info.get("description")
                default = self._get_effective_default(var, template_defaults, values)

                # Build prompt text and rely on show_default to display the default value
                prompt_text = f"{prompt}"

                # If variable is accessed with subscripts in the template, always prompt for each key and store as dict
                subs = used_subscripts.get(var, set()) if used_subscripts else set()
                if subs:
                    # Print all default values for subscripted keys before prompting
                    for k in subs:
                        key_default = None
                        if isinstance(default, dict):
                            key_default = default.get(k)
                        elif default is not None:
                            key_default = default
                        typer.secho(f"{display_name}['{k}']: ", fg=typer.colors.BRIGHT_BLACK, nl=False)
                        typer.secho(f"{key_default}", fg=typer.colors.CYAN)
                    result_map = {}
                    for k in subs:
                        kval = Prompt.ask(f"Value for {display_name}['{k}']:", default=str(default.get(k)) if isinstance(default, dict) and default.get(k) is not None else None, show_default=True)
                        result_map[k] = self._guess_and_cast(kval)
                    values[var] = result_map
                    continue

                if vtype == "bool":
                    # Normalize default to bool
                    bool_default = False
                    if isinstance(default, bool):
                        bool_default = default
                    elif isinstance(default, str):
                        bool_default = default.lower() in ("true", "1", "yes")
                    elif isinstance(default, int):
                        bool_default = default != 0
                    val = self.ask_bool(prompt_text, default=bool_default, description=description)
                elif vtype == "int":
                    # Use IntPrompt to validate and parse integers; show default if present
                    int_default = None
                    if isinstance(default, int):
                        int_default = default
                    elif isinstance(default, str) and default.isdigit():
                        int_default = int(default)
                    val = self.ask_int(prompt_text, default=int_default, description=description)
                else:
                    # Use Prompt for string input and show default
                    str_default = str(default) if default is not None else None
                    val = self.ask_str(prompt_text, default=str_default, show_default=True, description=description)

                # Handle collection types: arrays and maps
                if vtype in ("array", "list"):
                    values[var] = self.prompt_array(var, meta_info, default)
                    continue

                if vtype in ("map", "dict"):
                    # If the template indexes this variable with specific keys, prompt per-key
                    subs = used_subscripts.get(var, set()) if used_subscripts else set()
                    if subs:
                        # Prompt for each accessed key; allow single scalar default to apply to all
                        result_map = {}
                        # If default is a scalar, ask whether to expand it to accessed keys
                        if not isinstance(default, dict) and default is not None:
                            use_single = self.ask_bool(f"Use single value {default} for all {display_name} keys?", default=True)
                            if use_single:
                                for k in subs:
                                    result_map[k] = default
                                values[var] = result_map
                                continue
                        # Otherwise prompt per key or use metadata keys when present
                        keys_meta = meta_info.get("keys")
                        for k in subs:
                            if isinstance(keys_meta, dict) and k in keys_meta:
                                # reuse metadata prompt
                                kmeta = keys_meta[k]
                                result_map[k] = self.prompt_scalar(k, kmeta, kmeta.get("default"))
                            else:
                                # generic prompt
                                kval = self.ask_str(f"Value for {display_name}['{k}']:")
                                result_map[k] = self._guess_and_cast(kval)
                        values[var] = result_map
                        continue

                    # Fallback to full map prompting
                    values[var] = self.prompt_map(var, meta_info, default)
                    continue

                # store scalar/canonicalized value
                values[var] = self._cast_value_from_input(val, vtype)

        # Handle unknown variables. If a variable was already set (for
        # example by the set-level prompt mapping into `values[set_name]`),
        # don't prompt for it again.
        for var in used_vars:
            if var not in self._declared and var not in values:
                prompt_text = f"Value for '{var}':"
                val = Prompt.ask(prompt_text, default="", show_default=False)
                values[var] = self._guess_and_cast(val)

        return values

    def _get_effective_default(self, var_name: str, template_defaults: Dict[str, Any], current_values: Dict[str, Any]):
        # Prefer template-provided default, else declared metadata default
        meta_info = self._declared.get(var_name, ({}, {}))[1] if var_name in self._declared else {}
        candidate = None
        if template_defaults and var_name in template_defaults:
            candidate = template_defaults[var_name]
        else:
            candidate = meta_info.get("default") if isinstance(meta_info, dict) else None

        # If candidate names another variable and that variable has already
        # been provided by the user, use that value.
        if isinstance(candidate, str) and candidate in current_values:
            return current_values[candidate]

        # Otherwise, try to resolve identifier references to declared defaults
        if isinstance(candidate, str) and candidate in self._declared:
            decl_def = self._declared[candidate][1].get("default")
            if decl_def is not None:
                return decl_def

        return candidate

    def prompt_scalar(self, var_name: str, meta_info: Dict[str, Any], default_val: Any) -> Any:
        display_name = meta_info.get("display_name", var_name.replace("_", " ").title())
        vtype = meta_info.get("type", "str")
        prompt = meta_info.get("prompt", f"Enter {display_name}")
        description = meta_info.get("description")
        if vtype == "bool":
            bool_default = False
            if isinstance(default_val, bool):
                bool_default = default_val
            elif isinstance(default_val, str):
                bool_default = default_val.lower() in ("true", "1", "yes")
            elif isinstance(default_val, int):
                bool_default = default_val != 0
            return self.ask_bool(prompt, default=bool_default, description=description)
        if vtype == "int":
            int_default = None
            if isinstance(default_val, int):
                int_default = default_val
            elif isinstance(default_val, str) and default_val.isdigit():
                int_default = int(default_val)
            return self.ask_int(prompt, default=int_default, description=description)
        str_default = str(default_val) if default_val is not None else None
        return self.ask_str(prompt, default=str_default, show_default=True, description=description)

    def prompt_array(self, var_name: str, meta_info: Dict[str, Any], default_val: Any) -> Any:
        display_name = meta_info.get("display_name", var_name.replace("_", " ").title())
        item_type = meta_info.get("item_type", "str")
        item_prompt = meta_info.get("item_prompt", f"Enter {display_name} item")
        default_list = default_val if isinstance(default_val, list) else []
        default_count = len(default_list) if default_list else 0
        count = self.ask_int(f"How many entries for {display_name}?", default=default_count or 1)
        arr = []
        for i in range(count):
            item_default = default_list[i] if i < len(default_list) else None
            item_prompt_text = f"{item_prompt} [{i}]"
            if item_type == "int":
                int_d = item_default if isinstance(item_default, int) else (int(item_default) if isinstance(item_default, str) and str(item_default).isdigit() else None)
                item_val = self.ask_int(item_prompt_text, default=int_d)
            elif item_type == "bool":
                item_bool_d = self._cast_str_to_bool(item_default)
                item_val = self.ask_bool(item_prompt_text, default=item_bool_d)
            else:
                item_str_d = str(item_default) if item_default is not None else None
                item_val = self.ask_str(item_prompt_text, default=item_str_d, show_default=True)
            arr.append(self._cast_value_from_input(item_val, item_type))
        return arr

    def prompt_map(self, var_name: str, meta_info: Dict[str, Any], default_val: Any) -> Any:
        display_name = meta_info.get("display_name", var_name.replace("_", " ").title())
        keys_meta = meta_info.get("keys")
        result_map = {}
        if isinstance(keys_meta, dict):
            for key_name, kmeta in keys_meta.items():
                kdisplay = kmeta.get("display_name", f"{display_name}['{key_name}']")
                ktype = kmeta.get("type", "str")
                kdefault = kmeta.get("default") if "default" in kmeta else (default_val.get(key_name) if isinstance(default_val, dict) and key_name in default_val else None)
                kprompt = kmeta.get("prompt", f"Enter value for {kdisplay}")
                if ktype == "int":
                    kd = kdefault if isinstance(kdefault, int) else (int(kdefault) if isinstance(kdefault, str) and str(kdefault).isdigit() else None)
                    kval = self.ask_int(kprompt, default=kd)
                elif ktype == "bool":
                    kval = self.ask_bool(kprompt, default=self._cast_str_to_bool(kdefault))
                else:
                    kval = self.ask_str(kprompt, default=str(kdefault) if kdefault is not None else None, show_default=True)
                result_map[key_name] = self._cast_value_from_input(kval, ktype)
            return result_map
        if isinstance(default_val, dict) and len(default_val) > 0:
            for key_name, kdefault in default_val.items():
                kprompt = f"Enter value for {display_name}['{key_name}']"
                kval = self.ask_str(kprompt, default=str(kdefault) if kdefault is not None else None, show_default=True)
                result_map[key_name] = self._guess_and_cast(kval)
            return result_map
        count = self.ask_int(f"How many named entries for {display_name}?", default=1)
        for i in range(count):
            key_name = self.ask_str(f"Key name [{i}]", default=None, show_default=False)
            kval = self.ask_str(f"Value for {display_name}['{key_name}']:", default=None, show_default=False)
            result_map[key_name] = self._guess_and_cast(kval)
        return result_map

    @staticmethod
    def _cast_str_to_bool(s):
        if isinstance(s, bool):
            return s
        if isinstance(s, int):
            return s != 0
        if isinstance(s, str):
            return s.lower() in ("true", "1", "yes")
        return False

    @staticmethod
    def _cast_value_from_input(raw, vtype):
        if vtype == "int":
            try:
                return int(raw)
            except Exception:
                return raw
        if vtype == "bool":
            bool_val = PromptHandler._cast_str_to_bool(raw)
            return "true" if bool_val else "false"
        return raw

    @staticmethod
    def _guess_and_cast(raw):
        s = raw if not isinstance(raw, str) else raw.strip()
        if s == "":
            return raw
        if isinstance(s, str) and s.isdigit():
            return PromptHandler._cast_value_from_input(s, "int")
        if isinstance(s, str) and s.lower() in ("true", "false", "yes", "no", "1", "0", "t", "f"):
            return PromptHandler._cast_value_from_input(s, "bool")
        return PromptHandler._cast_value_from_input(s, "str")

    def prompt_scalar(self, var_name: str, meta_info: Dict[str, Any], default_val: Any) -> Any:
        display_name = meta_info.get("display_name", var_name.replace("_", " ").title())
        vtype = meta_info.get("type", "str")
        prompt = meta_info.get("prompt", f"Enter {display_name}")
        description = meta_info.get("description")
        if vtype == "bool":
            bool_default = False
            if isinstance(default_val, bool):
                bool_default = default_val
            elif isinstance(default_val, str):
                bool_default = default_val.lower() in ("true", "1", "yes")
            elif isinstance(default_val, int):
                bool_default = default_val != 0
            return self.ask_bool(prompt, default=bool_default, description=description)
        if vtype == "int":
            int_default = None
            if isinstance(default_val, int):
                int_default = default_val
            elif isinstance(default_val, str) and default_val.isdigit():
                int_default = int(default_val)
            return self.ask_int(prompt, default=int_default, description=description)
        str_default = str(default_val) if default_val is not None else None
        return self.ask_str(prompt, default=str_default, show_default=True, description=description)

    def prompt_array(self, var_name: str, meta_info: Dict[str, Any], default_val: Any) -> Any:
        display_name = meta_info.get("display_name", var_name.replace("_", " ").title())
        item_type = meta_info.get("item_type", "str")
        item_prompt = meta_info.get("item_prompt", f"Enter {display_name} item")
        default_list = default_val if isinstance(default_val, list) else []
        default_count = len(default_list) if default_list else 0
        count = self.ask_int(f"How many entries for {display_name}?", default=default_count or 1)
        arr = []
        for i in range(count):
            item_default = default_list[i] if i < len(default_list) else None
            item_prompt_text = f"{item_prompt} [{i}]"
            if item_type == "int":
                int_d = item_default if isinstance(item_default, int) else (int(item_default) if isinstance(item_default, str) and str(item_default).isdigit() else None)
                item_val = self.ask_int(item_prompt_text, default=int_d)
            elif item_type == "bool":
                item_bool_d = self._cast_str_to_bool(item_default)
                item_val = self.ask_bool(item_prompt_text, default=item_bool_d)
            else:
                item_str_d = str(item_default) if item_default is not None else None
                item_val = self.ask_str(item_prompt_text, default=item_str_d, show_default=True)
            arr.append(self._cast_value_from_input(item_val, item_type))
        return arr

    def prompt_map(self, var_name: str, meta_info: Dict[str, Any], default_val: Any) -> Any:
        display_name = meta_info.get("display_name", var_name.replace("_", " ").title())
        keys_meta = meta_info.get("keys")
        result_map = {}
        if isinstance(keys_meta, dict):
            for key_name, kmeta in keys_meta.items():
                kdisplay = kmeta.get("display_name", f"{display_name}['{key_name}']")
                ktype = kmeta.get("type", "str")
                kdefault = kmeta.get("default") if "default" in kmeta else (default_val.get(key_name) if isinstance(default_val, dict) and key_name in default_val else None)
                kprompt = kmeta.get("prompt", f"Enter value for {kdisplay}")
                if ktype == "int":
                    kd = kdefault if isinstance(kdefault, int) else (int(kdefault) if isinstance(kdefault, str) and str(kdefault).isdigit() else None)
                    kval = self.ask_int(kprompt, default=kd)
                elif ktype == "bool":
                    kval = self.ask_bool(kprompt, default=self._cast_str_to_bool(kdefault))
                else:
                    kval = self.ask_str(kprompt, default=str(kdefault) if kdefault is not None else None, show_default=True)
                result_map[key_name] = self._cast_value_from_input(kval, ktype)
            return result_map
        if isinstance(default_val, dict) and len(default_val) > 0:
            for key_name, kdefault in default_val.items():
                kprompt = f"Enter value for {display_name}['{key_name}']"
                kval = self.ask_str(kprompt, default=str(kdefault) if kdefault is not None else None, show_default=True)
                result_map[key_name] = self._guess_and_cast(kval)
            return result_map
        count = self.ask_int(f"How many named entries for {display_name}?", default=1)
        for i in range(count):
            key_name = self.ask_str(f"Key name [{i}]", default=None, show_default=False)
            kval = self.ask_str(f"Value for {display_name}['{key_name}']:", default=None, show_default=False)
            result_map[key_name] = self._guess_and_cast(kval)
        return result_map

    @staticmethod
    def _cast_str_to_bool(s):
        if isinstance(s, bool):
            return s
        if isinstance(s, int):
            return s != 0
        if isinstance(s, str):
            return s.lower() in ("true", "1", "yes")
        return False

    @staticmethod
    def _cast_value_from_input(raw, vtype):
        if vtype == "int":
            try:
                return int(raw)
            except Exception:
                return raw
        if vtype == "bool":
            bool_val = PromptHandler._cast_str_to_bool(raw)
            return "true" if bool_val else "false"
        return raw

    @staticmethod
    def _guess_and_cast(raw):
        s = raw if not isinstance(raw, str) else raw.strip()
        if s == "":
            return raw
        if isinstance(s, str) and s.isdigit():
            return PromptHandler._cast_value_from_input(s, "int")
        if isinstance(s, str) and s.lower() in ("true", "false", "yes", "no", "1", "0", "t", "f"):
            return PromptHandler._cast_value_from_input(s, "bool")
        return PromptHandler._cast_value_from_input(s, "str")
