"""Tests for managed library repository sync behavior."""

from __future__ import annotations

from pathlib import Path

from cli.core import repo


def test_clone_or_pull_repo_replaces_checkout_when_origin_changes(monkeypatch, tmp_path: Path) -> None:
    """Existing managed checkouts should be replaced when config points at a new remote."""
    target_path = tmp_path / "default"
    (target_path / ".git").mkdir(parents=True)

    clone_calls: list[tuple[str, str, Path, str | None, str | None, str]] = []

    def fake_get_repo_remote_url(_target_path: Path) -> str:
        return "https://github.com/christianlempa/boilerplates.git"

    def fake_replace_repo_checkout(
        name: str,
        url: str,
        target_path: Path,
        branch: str | None,
        sparse_dir: str | None,
        *,
        reason: str,
    ) -> tuple[bool, str]:
        clone_calls.append((name, url, target_path, branch, sparse_dir, reason))
        return True, "recloned"

    monkeypatch.setattr(repo, "_get_repo_remote_url", fake_get_repo_remote_url)
    monkeypatch.setattr(repo, "_replace_repo_checkout", fake_replace_repo_checkout)

    success, message = repo._clone_or_pull_repo(
        "default",
        "https://github.com/christianlempa/boilerplates-library.git",
        target_path,
        branch="main",
        sparse_dir=".",
    )

    assert success is True
    assert message == "recloned"
    assert clone_calls == [
        (
            "default",
            "https://github.com/christianlempa/boilerplates-library.git",
            target_path,
            "main",
            ".",
            "configured remote changed from https://github.com/christianlempa/boilerplates.git to "
            "https://github.com/christianlempa/boilerplates-library.git",
        )
    ]


def test_clone_or_pull_repo_replaces_checkout_after_diverged_pull(monkeypatch, tmp_path: Path) -> None:
    """Fast-forward failures should fall back to a fresh managed clone."""
    target_path = tmp_path / "default"
    (target_path / ".git").mkdir(parents=True)

    clone_calls: list[str] = []

    monkeypatch.setattr(
        repo, "_get_repo_remote_url", lambda _target_path: "git@github.com:ChristianLempa/boilerplates-library.git"
    )
    monkeypatch.setattr(
        repo,
        "_pull_repo_updates",
        lambda _name, _target_path, _branch: (
            False,
            "Pull failed: fatal: Not possible to fast-forward, aborting.",
        ),
    )

    def fake_replace_repo_checkout(
        name: str,
        url: str,
        target_path: Path,
        branch: str | None,
        sparse_dir: str | None,
        *,
        reason: str,
    ) -> tuple[bool, str]:
        clone_calls.append(reason)
        return True, "recloned after divergence"

    monkeypatch.setattr(repo, "_replace_repo_checkout", fake_replace_repo_checkout)

    success, message = repo._clone_or_pull_repo(
        "default",
        "https://github.com/christianlempa/boilerplates-library.git",
        target_path,
        branch="main",
        sparse_dir=".",
    )

    assert success is True
    assert message == "recloned after divergence"
    assert clone_calls == ["managed checkout diverged from origin"]
