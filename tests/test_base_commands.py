"""Focused regression tests for module base commands."""

from __future__ import annotations

from types import SimpleNamespace

from cli.core.module.base_commands import GenerationConfig, generate_template, list_templates


class _DisplayCapture:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.templates = SimpleNamespace(
            render_template_header=lambda *args, **kwargs: None,
            render_file_tree=lambda *args, **kwargs: None,
        )
        self.variables = SimpleNamespace(render_variables_table=lambda *args, **kwargs: None)

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


def test_generate_template_dry_run_skips_destination_prompt_and_overwrite_check(
    monkeypatch,
) -> None:
    """Dry runs without explicit destinations should not ask where to write or confirm overwrites."""
    display = _DisplayCapture()
    template = SimpleNamespace(id="whoami", slug="whoami")
    module_instance = SimpleNamespace(name="compose", display=display)

    monkeypatch.setattr("cli.core.module.base_commands._prepare_template", lambda *args, **kwargs: template)
    monkeypatch.setattr(
        "cli.core.module.base_commands._render_template",
        lambda *args, **kwargs: ({"compose.yaml": "services:\n"}, {}),
    )
    monkeypatch.setattr(
        "cli.core.module.base_commands.prompt_generation_destination",
        lambda slug: (_ for _ in ()).throw(AssertionError(f"prompt_generation_destination called for {slug}")),
    )
    monkeypatch.setattr(
        "cli.core.module.base_commands.check_output_directory",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("check_output_directory should not run")),
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
