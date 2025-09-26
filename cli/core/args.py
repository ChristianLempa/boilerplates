from typing import Dict, List

# NOTE: This helper supports both syntaxes:
#   --var KEY=VALUE
#   --var KEY VALUE
# It also tolerates passing values via ctx.args when using allow_extra_args.

def parse_var_inputs(var_items: List[str], extra_args: List[str]) -> Dict[str, str]:
  overrides: Dict[str, str] = {}

  # First, parse items collected by Typer's --var Option (usually KEY=VALUE forms)
  for item in var_items:
    if item is None:
      continue
    if "=" in item:
      key, value = item.split("=", 1)
      if key:
        overrides[key] = value
    else:
      # If user provided just a key via --var KEY, try to find the next value in extra args
      key = item
      value = _pop_next_value(extra_args)
      overrides[key] = value if value is not None else ""

  # Next, scan extra_args for any leftover --var occurrences using space-separated form
  i = 0
  while i < len(extra_args):
    tok = extra_args[i]
    if tok in ("--var", "-v"):
      name = None
      value = None
      # name may be next token; it can also be name=value
      if i + 1 < len(extra_args):
        nxt = extra_args[i + 1]
        if "=" in nxt:
          name, value = nxt.split("=", 1)
          i += 1
        else:
          name = nxt
          if i + 2 < len(extra_args):
            valtok = extra_args[i + 2]
            if not valtok.startswith("-"):
              value = valtok
              i += 2
            else:
              i += 1
          else:
            i += 1
      if name:
        overrides[name] = value if value is not None else ""
    elif tok.startswith("--var=") or tok.startswith("-v="):
      remainder = tok.split("=", 1)[1]
      if "=" in remainder:
        name, value = remainder.split("=", 1)
      else:
        name, value = remainder, _pop_next_value(extra_args[i + 1:])
      if name:
        overrides[name] = value if value is not None else ""
    i += 1

  return overrides


def _pop_next_value(args: List[str]) -> str | None:
  """Return the first non-flag token from args, if any, without modifying caller's list.
  This is a best-effort for --var KEY VALUE when Typer didn't bind VALUE to --var.
  """
  for tok in args:
    if not tok.startswith("-"):
      return tok
  return None
