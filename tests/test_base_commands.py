"""Focused regression tests for module base commands."""

from __future__ import annotations

from types import SimpleNamespace

from cli.core.module.base_commands import list_templates


class _DisplayCapture:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def text(self, value: str, style: str | None = None) -> None:
        del style
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
