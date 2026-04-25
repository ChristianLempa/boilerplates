from __future__ import annotations

import json
from pathlib import Path

from cli.core.template import Template
from cli.core.validation import (
    AnsibleValidator,
    DependencyMatrixBuilder,
    KindValidationResult,
    MatrixOptions,
    ValidationRunner,
)


def _write_template(tmp_path: Path, manifest: dict, files: dict[str, str]) -> Template:
    template_dir = tmp_path / "sample-compose"
    files_dir = template_dir / "files"
    files_dir.mkdir(parents=True)

    (template_dir / "template.json").write_text(json.dumps(manifest), encoding="utf-8")
    for relative_path, content in files.items():
        output_path = files_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    return Template(template_dir, library_name="test", library_type="static")


def test_dependency_matrix_covers_bool_and_enum_branches(tmp_path: Path) -> None:
    template = _write_template(
        tmp_path,
        {
            "kind": "compose",
            "slug": "sample-compose",
            "metadata": {
                "name": "Sample",
                "description": "Sample",
                "author": "test",
                "date": "2026-01-01",
            },
            "variables": [
                {
                    "name": "general",
                    "title": "General",
                    "items": [
                        {"name": "service_name", "type": "str", "default": "app"},
                        {
                            "name": "network_mode",
                            "type": "enum",
                            "default": "bridge",
                            "config": {"options": ["bridge", "host", "macvlan"]},
                        },
                    ],
                },
                {
                    "name": "traefik",
                    "title": "Traefik",
                    "toggle": "traefik_enabled",
                    "needs": "network_mode=bridge,macvlan",
                    "items": [
                        {"name": "traefik_enabled", "type": "bool", "default": False},
                        {"name": "traefik_host", "type": "str", "default": "app.example.com"},
                    ],
                },
            ],
        },
        {
            "compose.yaml": """
services:
  << service_name >>:
    image: nginx:1.25.3
<% if traefik_enabled %>
    labels:
      - traefik.http.routers.<< service_name >>.rule=Host(`<< traefik_host >>`)
<% endif %>
""",
        },
    )

    cases = DependencyMatrixBuilder(template, MatrixOptions(max_combinations=20)).build()
    rendered_values = [case.variables.get_satisfied_values() for case in cases]

    assert any(values.get("network_mode") == "bridge" for values in rendered_values)
    assert any(values.get("network_mode") == "macvlan" for values in rendered_values)
    assert any(values.get("traefik_enabled") is True for values in rendered_values)
    assert any(case.overrides.get("traefik_enabled") is False for case in cases)


def test_validation_runner_reports_semantic_failure_for_matrix_case(tmp_path: Path) -> None:
    template = _write_template(
        tmp_path,
        {
            "kind": "compose",
            "slug": "broken-compose",
            "metadata": {
                "name": "Broken",
                "description": "Broken",
                "author": "test",
                "date": "2026-01-01",
            },
            "variables": [
                {
                    "name": "general",
                    "title": "General",
                    "items": [
                        {"name": "service_name", "type": "str", "default": "app"},
                        {"name": "invalid_enabled", "type": "bool", "default": False},
                    ],
                }
            ],
        },
        {
            "compose.yaml": """
<% if invalid_enabled %>
services: []
<% else %>
services:
  << service_name >>:
    image: nginx:1.25.3
<% endif %>
""",
        },
    )

    cases = DependencyMatrixBuilder(template, MatrixOptions(max_combinations=10)).build()
    summary = ValidationRunner(template, cases, semantic=True).run()

    assert not summary.ok
    assert any(failure.stage == "sem" and failure.file_path == "compose.yaml" for failure in summary.failures)


def test_validation_runner_treats_unavailable_kind_validator_as_skip(tmp_path: Path) -> None:
    template = _write_template(
        tmp_path,
        {
            "kind": "custom",
            "slug": "custom-template",
            "metadata": {
                "name": "Custom",
                "description": "Custom",
                "author": "test",
                "date": "2026-01-01",
            },
            "variables": [
                {
                    "name": "general",
                    "title": "General",
                    "items": [{"name": "service_name", "type": "str", "default": "app"}],
                }
            ],
        },
        {"config.yaml": "name: << service_name >>\n"},
    )

    def unavailable_validator(_rendered_files: dict[str, str], _case_name: str) -> KindValidationResult:
        return KindValidationResult(
            validator="missing-tool",
            available=False,
            details=["Required command is unavailable: missing-tool"],
        )

    cases = DependencyMatrixBuilder(template, MatrixOptions(max_combinations=10)).build()
    summary = ValidationRunner(template, cases, semantic=True, kind_validator=unavailable_validator).run()

    assert summary.ok
    assert summary.kind_available is False
    assert summary.kind_skipped_cases == {"defaults"}
    assert summary.failures == []


def test_ansible_validator_detects_main_yml_playbook_by_hosts_key(tmp_path: Path) -> None:
    playbook = tmp_path / "main.yml"
    playbook.write_text("- name: Configure host\n  hosts: all\n  tasks: []\n", encoding="utf-8")

    assert AnsibleValidator._find_playbooks(tmp_path) == [playbook]


def test_ansible_validator_classifies_missing_collection_as_dependency_resolution_failure() -> None:
    assert AnsibleValidator._is_dependency_resolution_failure("ERROR! the role 'vendor.role' was not found")
    assert AnsibleValidator._is_dependency_resolution_failure("ERROR! couldn't resolve module/action 'vendor.module'")
    assert not AnsibleValidator._is_dependency_resolution_failure("ERROR! Syntax Error while loading YAML")
