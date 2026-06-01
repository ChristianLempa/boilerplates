"""Tests for generation destination resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from cli.core.input import InputManager
from cli.core.module.generation_destination import (
    build_remote_shell_path,
    build_scp_remote_target,
    prompt_generation_destination,
    resolve_cli_destination,
    resolve_remote_upload_target,
)


def test_resolve_cli_destination_uses_remote_defaults() -> None:
    """Remote generation should default the remote path to the template slug."""
    destination = resolve_cli_destination(
        output=None,
        remote="deploy",
        remote_path=None,
        slug="whoami",
    )

    assert destination is not None
    assert destination.is_remote is True
    assert destination.remote_host == "deploy"
    assert destination.remote_path == "~/whoami"


def test_resolve_cli_destination_rejects_mixed_local_and_remote_flags() -> None:
    """Local and remote destination flags are mutually exclusive."""
    with pytest.raises(ValueError, match="either --output"):
        resolve_cli_destination(
            output="./out",
            remote="deploy",
            remote_path=None,
            slug="whoami",
        )


def test_build_remote_shell_path_quotes_home_paths_with_spaces() -> None:
    """SSH mkdir paths should stay safe when the target contains spaces."""
    assert build_remote_shell_path("~/My Dir/app", trailing_slash=True) == "\"$HOME\"/'My Dir/app/'"


def test_build_scp_remote_target_preserves_home_expansion() -> None:
    """SCP targets should quote already-resolved absolute paths safely."""
    assert (
        build_scp_remote_target("deploy", "/home/test/My Dir/app", trailing_slash=True)
        == "deploy:'/home/test/My Dir/app/'"
    )


def test_resolve_remote_upload_target_expands_home_via_ssh(monkeypatch: pytest.MonkeyPatch) -> None:
    """SCP uploads should resolve ~ to the remote home directory before copying."""

    class _Result:
        def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(args: list[str], check: bool, capture_output: bool, text: bool) -> _Result:
        del check, capture_output, text
        assert args == ["ssh", "deploy", "printf '%s' \"$HOME\""]
        return _Result(returncode=0, stdout="/home/deploy")

    monkeypatch.setattr("cli.core.module.generation_destination.subprocess.run", fake_run)

    assert resolve_remote_upload_target("deploy", "~/dockhand", trailing_slash=True) == "deploy:/home/deploy/dockhand/"


def test_numbered_choice_accepts_numeric_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Numbered choices should accept the displayed index."""
    responses = iter(["2"])

    def fake_ask(*args: Any, **kwargs: Any) -> str:
        del args, kwargs
        return next(responses)

    monkeypatch.setattr("cli.core.input.input_manager.Prompt.ask", fake_ask)

    input_mgr = InputManager()

    assert input_mgr.numbered_choice("Store generated template in", ["local", "remote"], default="local") == "remote"


def test_numbered_choice_uses_numeric_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Numbered choices should display a clean numeric default."""
    captured: dict[str, Any] = {}

    def fake_ask(prompt: str, default: str = "", show_default: bool = False, **kwargs: Any) -> str:
        del prompt, kwargs
        captured["default"] = default
        captured["show_default"] = show_default
        return ""

    monkeypatch.setattr("cli.core.input.input_manager.Prompt.ask", fake_ask)

    input_mgr = InputManager()

    assert input_mgr.numbered_choice("Store generated template in", ["local", "remote"], default="local") == "local"
    assert captured == {"default": "1", "show_default": True}


def test_prompt_generation_destination_uses_numbered_choice_for_local(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Interactive destination selection should resolve local output via numbered choices."""
    calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def fake_numbered_choice(self, prompt: str, choices: list[str], default: str | None = None) -> str:
        calls.append(("numbered_choice", (prompt, tuple(choices)), {"default": default}))
        del self
        return "local"

    def fake_text(self, prompt: str, default: str | None = None, **kwargs: Any) -> str:
        calls.append(("text", (prompt,), {"default": default, **kwargs}))
        del self
        return str(tmp_path / "whoami")

    monkeypatch.setattr(InputManager, "numbered_choice", fake_numbered_choice)
    monkeypatch.setattr(InputManager, "text", fake_text)

    destination = prompt_generation_destination("whoami")

    assert destination.mode == "local"
    assert destination.local_output_dir == tmp_path / "whoami"
    assert calls[0] == (
        "numbered_choice",
        ("Store generated template in", ("local", "remote")),
        {"default": "local"},
    )
    assert calls[1] == (
        "text",
        ("Local output directory",),
        {"default": str(Path.cwd() / "whoami")},
    )


def test_prompt_generation_destination_asks_for_remote_host_and_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Interactive remote destination should use direct text prompts for host and path."""
    calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
    responses = iter(["srv-test-1.home.clcreative.de", "~/dockhand"])

    def fake_numbered_choice(self, prompt: str, choices: list[str], default: str | None = None) -> str:
        calls.append(("numbered_choice", (prompt, tuple(choices)), {"default": default}))
        del self
        return "remote"

    def fake_text(self, prompt: str, default: str | None = None, **kwargs: Any) -> str:
        calls.append(("text", (prompt,), {"default": default, **kwargs}))
        del self
        return next(responses)

    monkeypatch.setattr(InputManager, "numbered_choice", fake_numbered_choice)
    monkeypatch.setattr(InputManager, "text", fake_text)

    destination = prompt_generation_destination("dockhand")

    assert destination.mode == "remote"
    assert destination.remote_host == "srv-test-1.home.clcreative.de"
    assert destination.remote_path == "~/dockhand"
    assert calls == [
        ("numbered_choice", ("Store generated template in", ("local", "remote")), {"default": "local"}),
        ("text", ("Remote server host or IP address",), {"default": None}),
        ("text", ("Remote target directory",), {"default": "~/dockhand"}),
    ]
