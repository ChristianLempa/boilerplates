"""Regression tests for prompt handling."""

from __future__ import annotations

from typing import Any

import pytest

from cli.core.input.prompt_manager import PromptHandler
from cli.core.template.variable import Variable

TEST_REQUIRED_INTEGER = 42


@pytest.mark.parametrize(
    "variable_data",
    [
        {"name": "puid", "type": "int"},
        {"name": "database_type", "type": "enum", "config": {"options": ["sqlite", "postgres"]}},
        {"name": "disable_local_login", "type": "bool"},
    ],
)
def test_optional_prompt_allows_blank_input(
    monkeypatch: pytest.MonkeyPatch,
    variable_data: dict[str, Any],
) -> None:
    """Optional variables without defaults should accept an empty response."""
    prompts: list[dict[str, Any]] = []

    def fake_ask(prompt_text: str, default: str = "", show_default: bool = False, **kwargs: Any) -> str:
        prompts.append(
            {
                "prompt_text": prompt_text,
                "default": default,
                "show_default": show_default,
                **kwargs,
            }
        )
        return ""

    monkeypatch.setattr("cli.core.input.prompt_manager.Prompt.ask", fake_ask)

    variable = Variable(variable_data)
    prompt_handler = PromptHandler()
    raw_value = prompt_handler._prompt_variable(variable)

    assert raw_value is None
    assert prompts
    assert prompts[0]["default"] == ""
    assert prompts[0]["show_default"] is False


def test_required_integer_without_default_still_uses_integer_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Required integers should still use the integer prompt path instead of accepting blank input."""
    calls: list[tuple[str, Any]] = []

    def fake_integer(self, prompt: str, default: int | None = None, **kwargs: Any) -> int:
        del self, kwargs
        calls.append((prompt, default))
        return TEST_REQUIRED_INTEGER

    monkeypatch.setattr("cli.core.input.prompt_manager.InputManager.integer", fake_integer)

    variable = Variable({"name": "ports_http", "type": "int", "required": True})
    prompt_handler = PromptHandler()

    assert prompt_handler._prompt_variable(variable) == TEST_REQUIRED_INTEGER
    assert calls


@pytest.mark.parametrize("origin", ["config", "var-file", "cli"])
def test_applied_optional_string_defaults_are_shown_and_preserved(
    monkeypatch: pytest.MonkeyPatch,
    origin: str,
) -> None:
    """Applied defaults from external sources should be visible in prompts and kept on Enter."""
    prompts: list[dict[str, Any]] = []

    def fake_ask(prompt_text: str, default: str = "", show_default: bool = False, **kwargs: Any) -> str:
        prompts.append(
            {
                "prompt_text": prompt_text,
                "default": default,
                "show_default": show_default,
                **kwargs,
            }
        )
        return default

    monkeypatch.setattr("cli.core.input.prompt_manager.Prompt.ask", fake_ask)

    variable = Variable({"name": "service_name", "type": "str"})
    variable.value = "grafana"
    variable.origin = origin

    prompt_handler = PromptHandler()
    raw_value = prompt_handler._prompt_variable(variable)

    assert raw_value == "grafana"
    assert prompts
    assert prompts[0]["default"] == "grafana"
    assert prompts[0]["show_default"] is True


@pytest.mark.parametrize("origin", ["config", "var-file", "cli"])
def test_applied_optional_bool_defaults_are_shown_and_preserved(
    monkeypatch: pytest.MonkeyPatch,
    origin: str,
) -> None:
    """Applied boolean defaults should use confirm prompts with the current value as default."""
    calls: list[tuple[str, Any]] = []

    def fake_confirm(self, prompt: str, default: bool | None = None) -> bool:
        del self
        calls.append((prompt, default))
        assert default is True
        return default

    monkeypatch.setattr("cli.core.input.prompt_manager.InputManager.confirm", fake_confirm)

    variable = Variable({"name": "traefik_enabled", "type": "bool"})
    variable.value = True
    variable.origin = origin

    prompt_handler = PromptHandler()

    assert prompt_handler._prompt_variable(variable) is True
    assert calls
