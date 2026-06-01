"""Focused regression tests for module base commands."""

from __future__ import annotations

from types import SimpleNamespace

from cli.core.module.base_commands import (
    GenerationConfig,
    ValidationConfig,
    _validate_all_templates,
    apply_output_name,
    generate_template,
    list_templates,
    validate_templates,
)


def _noop(*_args, **_kwargs) -> None:
    return None


def _raise_destination_prompt(slug: str):
    raise AssertionError(f"prompt_generation_destination called for {slug}")


def _raise_output_check(*_args, **_kwargs):
    raise AssertionError("check_output_directory should not run")


class _DisplayCapture:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.templates = SimpleNamespace(
            render_template_header=_noop,
            render_file_tree=_noop,
        )
        self.variables = SimpleNamespace(render_variables_table=_noop)

    def text(self, value: str, style: str | None = None) -> None:
        del style
        self.lines.append(value)

    def success(self, value: str, *args, **kwargs) -> None:
        del args, kwargs
        self.lines.append(value)

    def warning(self, value: str, *args, **kwargs) -> None:
        del args, kwargs
        self.lines.append(value)

    def error(self, value: str, *args, **kwargs) -> None:
        del args, kwargs
        self.lines.append(value)

    def data_table(self, *args, **kwargs) -> None:
        del args, kwargs
        raise AssertionError("data_table should not be used for raw output")

    def info(self, *args, **kwargs) -> None:
        del args, kwargs
        raise AssertionError("info should not be used when templates exist")


class _ValidationDisplayCapture(_DisplayCapture):
    def data_table(self, *args, **kwargs) -> None:
        del args, kwargs
        self.lines.append("data_table")

    def info(self, value: str = "", *args, **kwargs) -> None:
        del args, kwargs
        self.lines.append(value)


def test_list_templates_raw_outputs_tab_separated_rows() -> None:
    """Raw listing should emit one tab-separated row per template."""
    template = SimpleNamespace(
        id="whoami",
        metadata=SimpleNamespace(
            name="Whoami",
            tags=["docker", "test"],
            version=SimpleNamespace(name="1.0.0"),
            library="default",
            library_type="git",
        ),
    )
    display = _DisplayCapture()
    module_instance = SimpleNamespace(
        name="compose",
        display=display,
        _load_all_templates=lambda: [template],
    )

    returned_templates = list_templates(module_instance, raw=True)

    assert returned_templates == [template]
    assert display.lines == ["whoami\tWhoami\tdocker,test\t1.0.0\tdefault"]


def test_apply_output_name_renames_top_level_paths_only() -> None:
    """Named generation should rename top-level outputs while preserving nested names."""
    rendered_files = {
        "files/test.txt": "nested",
        "main.tf": "main",
        "dns.tf": "dns",
    }

    assert apply_output_name(rendered_files, "servertest1") == {
        "servertest1_files/test.txt": "nested",
        "servertest1.tf": "main",
        "servertest1_dns.tf": "dns",
    }


def test_generate_template_applies_output_name_before_writing(monkeypatch, tmp_path) -> None:
    """Generate should write renamed paths when --name is provided."""
    display = _DisplayCapture()
    template = SimpleNamespace(id="terraform", slug="terraform")
    module_instance = SimpleNamespace(name="terraform", display=display)
    written: dict[str, object] = {}

    monkeypatch.setattr("cli.core.module.base_commands._prepare_template", lambda *_args, **_kwargs: template)
    monkeypatch.setattr(
        "cli.core.module.base_commands._render_template",
        lambda *_args, **_kwargs: ({"files/test.txt": "nested", "main.tf": "main", "dns.tf": "dns"}, {}),
    )
    monkeypatch.setattr("cli.core.module.base_commands.check_output_directory", lambda *_args, **_kwargs: [])

    def capture_write(output_dir, rendered_files):
        written["output_dir"] = output_dir
        written["rendered_files"] = rendered_files

    monkeypatch.setattr("cli.core.module.base_commands.write_rendered_files", capture_write)

    generate_template(
        module_instance,
        GenerationConfig(
            id="terraform",
            output=str(tmp_path),
            interactive=False,
            name="servertest1",
        ),
    )

    assert written["output_dir"] == tmp_path
    assert written["rendered_files"] == {
        "servertest1_files/test.txt": "nested",
        "servertest1.tf": "main",
        "servertest1_dns.tf": "dns",
    }


def test_generate_template_dry_run_skips_destination_prompt_and_overwrite_check(
    monkeypatch,
) -> None:
    """Dry runs without explicit destinations should not ask where to write or confirm overwrites."""
    display = _DisplayCapture()
    template = SimpleNamespace(id="whoami", slug="whoami")
    module_instance = SimpleNamespace(name="compose", display=display)

    monkeypatch.setattr("cli.core.module.base_commands._prepare_template", lambda *_args, **_kwargs: template)
    monkeypatch.setattr(
        "cli.core.module.base_commands._render_template",
        lambda *_args, **_kwargs: ({"compose.yaml": "services:\n"}, {}),
    )
    monkeypatch.setattr("cli.core.module.base_commands.prompt_generation_destination", _raise_destination_prompt)
    monkeypatch.setattr(
        "cli.core.module.base_commands.check_output_directory",
        _raise_output_check,
    )

    generate_template(
        module_instance,
        GenerationConfig(
            id="whoami",
            interactive=True,
            dry_run=True,
        ),
    )

    assert any("boilerplate rendered successfully" in line for line in display.lines)
    assert any("preview only" in line for line in display.lines)


def test_validate_templates_without_id_validates_all_templates(monkeypatch) -> None:
    """Omitting the template ID should keep the legacy validate-all behavior."""
    display = _ValidationDisplayCapture()
    module_instance = SimpleNamespace(name="compose", display=display)
    called = {}

    def capture_validate_all(received_module, received_config):
        called["module"] = received_module
        called["config"] = received_config

    monkeypatch.setattr("cli.core.module.base_commands._validate_all_templates", capture_validate_all)

    validate_templates(module_instance, None, None, ValidationConfig(verbose=False))

    assert called["module"] is module_instance
    assert called["config"].semantic is True


def test_validate_single_template_runs_default_semantic_validation(monkeypatch) -> None:
    """Single-template validation should still run semantic validation by default."""
    display = _ValidationDisplayCapture()
    template = SimpleNamespace(id="whoami", used_variables=[], variables=SimpleNamespace())
    module_instance = SimpleNamespace(name="compose", display=display)
    called = {}

    monkeypatch.setattr("cli.core.module.base_commands._load_template_for_validation", lambda *_args: template)

    def capture_semantic(received_module, received_template, verbose):
        called["module"] = received_module
        called["template"] = received_template
        called["verbose"] = verbose

    monkeypatch.setattr("cli.core.module.base_commands._run_semantic_validation", capture_semantic)

    validate_templates(module_instance, "whoami", None, ValidationConfig(verbose=False))

    assert called == {"module": module_instance, "template": template, "verbose": False}


def test_validate_all_templates_keeps_basic_validation_by_default(monkeypatch) -> None:
    """Validate-all should not start rendering every template semantically unless matrix/kind is requested."""
    display = _ValidationDisplayCapture()
    template = SimpleNamespace(id="whoami", used_variables=[], variables=SimpleNamespace())
    module_instance = SimpleNamespace(
        name="compose",
        display=display,
        _load_all_templates=lambda: [template],
    )

    monkeypatch.setattr("cli.core.module.base_commands._run_semantic_validation", _raise_output_check)

    _validate_all_templates(module_instance, ValidationConfig(verbose=False))

    assert any("All templates are valid" in line for line in display.lines)
