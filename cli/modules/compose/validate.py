"""Docker Compose validation functionality."""

import logging
import subprocess
import tempfile
from pathlib import Path

from typer import Exit

from ...core.template import Template

logger = logging.getLogger(__name__)


def run_docker_validation(
    module_instance,
    template_id: str | None,
    path: str | None,
    test_all: bool,
    verbose: bool,
) -> None:
    """Run Docker Compose validation using docker compose config.

    Args:
        module_instance: The module instance (for display and template loading)
        template_id: Template ID to validate
        path: Path to template directory
        test_all: Test all variable combinations
        verbose: Show detailed output

    Raises:
        Exit: If validation fails or docker is not available
    """
    try:
        # Load the template
        if path:
            template_path = Path(path).resolve()
            template = Template(template_path, library_name="local")
        else:
            template = module_instance._load_template_by_id(template_id)

        module_instance.display.info("")
        module_instance.display.info("Running Docker Compose validation...")

        # Test multiple combinations or single configuration
        if test_all:
            _test_variable_combinations(module_instance, template, verbose)
        else:
            # Single configuration with template defaults
            success = _validate_compose_files(
                module_instance, template, template.variables, verbose, "Template defaults"
            )
            if success:
                module_instance.display.success("Docker Compose validation passed")
            else:
                module_instance.display.error("Docker Compose validation failed")
                raise Exit(code=1) from None

    except FileNotFoundError as e:
        module_instance.display.error(
            "Docker Compose CLI not found",
            context="Install Docker Desktop or Docker Engine with Compose plugin",
        )
        raise Exit(code=1) from e
    except Exception as e:
        module_instance.display.error(f"Docker validation failed: {e}")
        raise Exit(code=1) from e


def _validate_compose_files(module_instance, template, variables, verbose: bool, config_name: str) -> bool:
    """Validate rendered compose files using docker compose config.

    Args:
        module_instance: The module instance
        template: The template object
        variables: VariableCollection with configured values
        verbose: Show detailed output
        config_name: Name of this configuration (for display)

    Returns:
        True if validation passed, False otherwise
    """
    try:
        # Render the template
        debug_mode = logger.isEnabledFor(logging.DEBUG)
        rendered_files, _ = template.render(variables, debug=debug_mode)

        # Find compose files
        compose_files = [
            (filename, content)
            for filename, content in rendered_files.items()
            if filename.endswith(("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"))
        ]

        if not compose_files:
            module_instance.display.warning(f"[{config_name}] No Docker Compose files found")
            return True

        # Validate each compose file
        has_errors = False
        for filename, content in compose_files:
            if verbose:
                module_instance.display.info(f"[{config_name}] Validating: {filename}")

            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name

            try:
                # Run docker compose config
                result = subprocess.run(
                    ["docker", "compose", "-f", tmp_path, "config", "--quiet"],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if result.returncode != 0:
                    has_errors = True
                    module_instance.display.error(f"[{config_name}] Docker validation failed for {filename}")
                    if result.stderr:
                        module_instance.display.info(f"\n{result.stderr}")
                elif verbose:
                    module_instance.display.success(f"[{config_name}] Docker validation passed: {filename}")

            finally:
                # Clean up temporary file
                Path(tmp_path).unlink(missing_ok=True)

        return not has_errors

    except Exception as e:
        module_instance.display.error(f"[{config_name}] Validation failed: {e}")
        return False


def _test_variable_combinations(module_instance, template, verbose: bool) -> None:
    """Test multiple variable combinations intelligently.

    Tests:
    1. Minimal config (all toggles OFF)
    2. Maximal config (all toggles ON)
    3. Each toggle individually ON (to isolate toggle-specific issues)

    Args:
        module_instance: The module instance
        template: The template object
        verbose: Show detailed output

    Raises:
        Exit: If any validation fails
    """
    module_instance.display.info("Testing multiple variable combinations...")
    module_instance.display.info("")

    # Find all boolean toggle variables
    toggle_vars = _find_toggle_variables(template)

    if not toggle_vars:
        module_instance.display.warning("No toggle variables found - testing default configuration only")
        success = _validate_compose_files(module_instance, template, template.variables, verbose, "Default")
        if not success:
            raise Exit(code=1) from None
        module_instance.display.success("Docker Compose validation passed")
        return

    module_instance.display.info(f"Found {len(toggle_vars)} toggle variable(s): {', '.join(toggle_vars)}")
    module_instance.display.info("")

    all_passed = True
    test_count = 0

    # Test 1: Minimal (all OFF)
    module_instance.display.info("[1/3] Testing minimal configuration (all toggles OFF)...")
    toggle_config = dict.fromkeys(toggle_vars, False)
    variables = _get_variables_with_toggles(module_instance, template, toggle_config)
    if not _validate_compose_files(module_instance, template, variables, verbose, "Minimal"):
        all_passed = False
    test_count += 1
    module_instance.display.info("")

    # Test 2: Maximal (all ON)
    module_instance.display.info("[2/3] Testing maximal configuration (all toggles ON)...")
    toggle_config = dict.fromkeys(toggle_vars, True)
    variables = _get_variables_with_toggles(module_instance, template, toggle_config)
    if not _validate_compose_files(module_instance, template, variables, verbose, "Maximal"):
        all_passed = False
    test_count += 1
    module_instance.display.info("")

    # Test 3: Each toggle individually
    module_instance.display.info(f"[3/3] Testing each toggle individually ({len(toggle_vars)} tests)...")
    for i, toggle in enumerate(toggle_vars, 1):
        # Set all OFF except the current one
        toggle_config = {t: t == toggle for t in toggle_vars}
        variables = _get_variables_with_toggles(module_instance, template, toggle_config)
        config_name = f"{toggle}=true"
        if not _validate_compose_files(module_instance, template, variables, verbose, config_name):
            all_passed = False
        test_count += 1
        if verbose and i < len(toggle_vars):
            module_instance.display.info("")

    # Summary
    module_instance.display.info("")
    module_instance.display.info("─" * 80)
    if all_passed:
        module_instance.display.success(f"All {test_count} configuration(s) passed Docker Compose validation")
    else:
        module_instance.display.error("Some configurations failed Docker Compose validation")
        raise Exit(code=1) from None


def _find_toggle_variables(template) -> list[str]:
    """Find all boolean toggle variables in a template.

    Args:
        template: The template object

    Returns:
        List of toggle variable names
    """
    toggle_vars = []
    for var_name, var in template.variables._variable_map.items():
        if var.type == "bool" and var_name.endswith("_enabled"):
            toggle_vars.append(var_name)
    return sorted(toggle_vars)


def _get_variables_with_toggles(module_instance, template, toggle_config: dict[str, bool]):  # noqa: ARG001
    """Get VariableCollection with specific toggle settings.

    Args:
        module_instance: The module instance (unused, for signature consistency)
        template: The template object
        toggle_config: Dict mapping toggle names to boolean values

    Returns:
        VariableCollection with configured toggle values
    """
    # Reload template to get fresh VariableCollection
    # (template.variables is mutated by previous calls)
    fresh_template = Template(template.template_dir, library_name=template.metadata.library)
    variables = fresh_template.variables

    # Apply toggle configuration
    for toggle_name, toggle_value in toggle_config.items():
        if toggle_name in variables._variable_map:
            variables._variable_map[toggle_name].value = toggle_value

    return variables
