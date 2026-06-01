"""Helpers for generation destinations and remote uploads."""

from __future__ import annotations

import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ..input import InputManager


@dataclass
class GenerationDestination:
    """Resolved generation target."""

    mode: str
    local_output_dir: Path | None = None
    remote_host: str | None = None
    remote_path: str | None = None

    @property
    def is_remote(self) -> bool:
        return self.mode == "remote"


def normalize_output_path(path_value: str) -> Path:
    """Normalize paths that look absolute but were provided without a leading slash."""
    output_dir = Path(path_value)
    if not output_dir.is_absolute() and str(output_dir).startswith(("Users/", "home/", "usr/", "opt/", "var/", "tmp/")):
        output_dir = Path("/") / output_dir
    return output_dir


def resolve_cli_destination(
    output: str | None,
    remote: str | None,
    remote_path: str | None,
    slug: str,
) -> GenerationDestination | None:
    """Resolve generation destination from explicit CLI flags only."""
    if output and remote:
        raise ValueError("Use either --output for a local directory or --remote for a remote server, not both")
    if remote_path and not remote:
        raise ValueError("--remote-path requires --remote")

    if remote:
        return GenerationDestination(
            mode="remote",
            remote_host=remote,
            remote_path=remote_path or f"~/{slug}",
        )

    if output:
        return GenerationDestination(mode="local", local_output_dir=normalize_output_path(output))

    return None


def prompt_generation_destination(slug: str) -> GenerationDestination:
    """Prompt for local or remote generation target."""
    input_mgr = InputManager()
    destination_mode = input_mgr.numbered_choice("Store generated template in", ["local", "remote"], default="local")

    if destination_mode == "local":
        local_default = str(Path.cwd() / slug)
        local_output = input_mgr.text("Local output directory", default=local_default).strip() or local_default
        return GenerationDestination(mode="local", local_output_dir=normalize_output_path(local_output))

    remote_host = input_mgr.text("Remote server host or IP address", default=None).strip()
    if not remote_host:
        raise ValueError("Remote server host or IP address cannot be empty")

    remote_default = f"~/{slug}"
    remote_path = input_mgr.text("Remote target directory", default=remote_default).strip() or remote_default
    return GenerationDestination(mode="remote", remote_host=remote_host, remote_path=remote_path)


def format_remote_destination(host: str, remote_path: str) -> str:
    """Format host/path for user-facing messages."""
    return f"{host}:{remote_path}"


def build_remote_shell_path(remote_path: str, trailing_slash: bool = False) -> str:
    """Build a shell-safe remote path expression for ssh/scp commands."""
    normalized = remote_path.rstrip("/")
    suffix = "/" if trailing_slash else ""

    if normalized in {"~", ""}:
        return f'"$HOME"{suffix}'

    if normalized.startswith("~/"):
        relative = normalized[2:]
        quoted_relative = shlex.quote(f"{relative}{suffix}")
        return f'"$HOME"/{quoted_relative}'

    return shlex.quote(f"{normalized}{suffix}")


def build_scp_remote_target(remote_host: str, remote_path: str, trailing_slash: bool = False) -> str:
    """Build an scp destination target for an already-resolved remote path."""
    normalized = remote_path.rstrip("/")
    suffix = "/" if trailing_slash else ""

    quoted_path = shlex.quote(f"{normalized}{suffix}")
    return f"{remote_host}:{quoted_path}"


def resolve_remote_home_directory(remote_host: str) -> str:
    """Resolve the remote user's home directory over SSH."""
    home_result = subprocess.run(
        ["ssh", remote_host, "printf '%s' \"$HOME\""],
        check=False,
        capture_output=True,
        text=True,
    )
    if home_result.returncode != 0:
        error_output = home_result.stderr.strip() or home_result.stdout.strip() or "SSH home resolution failed"
        raise RuntimeError(f"Failed to resolve remote home directory on '{remote_host}': {error_output}")

    remote_home = home_result.stdout.strip()
    if not remote_home:
        raise RuntimeError(f"Failed to resolve remote home directory on '{remote_host}': empty response")

    return remote_home


def resolve_remote_absolute_path(remote_host: str, remote_path: str, trailing_slash: bool = False) -> str:
    """Resolve ~-prefixed remote paths to absolute remote filesystem paths."""
    normalized = remote_path.rstrip("/")
    suffix = "/" if trailing_slash else ""

    if normalized not in {"~", ""} and not normalized.startswith("~/"):
        return f"{normalized}{suffix}"

    remote_home = resolve_remote_home_directory(remote_host)

    return f"{remote_home}{suffix}" if normalized in {"~", ""} else f"{remote_home}/{normalized[2:]}{suffix}"


def resolve_remote_upload_target(remote_host: str, remote_path: str, trailing_slash: bool = False) -> str:
    """Resolve remote paths to absolute scp targets."""
    absolute_path = resolve_remote_absolute_path(remote_host, remote_path, trailing_slash=trailing_slash)
    return build_scp_remote_target(remote_host, absolute_path, trailing_slash=trailing_slash)


def _write_staging_files(staging_dir: Path, rendered_files: dict[str, str]) -> None:
    """Write rendered files to a local staging directory."""
    staging_dir.mkdir(parents=True, exist_ok=True)
    for file_path, content in rendered_files.items():
        full_path = staging_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")


def write_rendered_files_remote(
    remote_host: str,
    remote_path: str,
    rendered_files: dict[str, str],
) -> None:
    """Upload rendered files to a remote host over SSH."""
    with tempfile.TemporaryDirectory(prefix="boilerplates-remote-") as staging_root:
        staging_dir = Path(staging_root)
        _write_staging_files(staging_dir, rendered_files)

        remote_mkdir_path = build_remote_shell_path(remote_path)
        remote_copy_target = resolve_remote_upload_target(remote_host, remote_path, trailing_slash=True)

        mkdir_result = subprocess.run(
            ["ssh", remote_host, f"mkdir -p -- {remote_mkdir_path}"],
            check=False,
            capture_output=True,
            text=True,
        )
        if mkdir_result.returncode != 0:
            error_output = mkdir_result.stderr.strip() or mkdir_result.stdout.strip() or "SSH mkdir failed"
            raise RuntimeError(f"Failed to prepare remote directory '{remote_path}' on '{remote_host}': {error_output}")

        upload_result = subprocess.run(
            ["scp", "-r", f"{staging_dir}/.", remote_copy_target],
            check=False,
            capture_output=True,
            text=True,
        )
        if upload_result.returncode != 0:
            error_output = upload_result.stderr.strip() or upload_result.stdout.strip() or "SCP upload failed"
            raise RuntimeError(f"Failed to upload files to '{remote_host}:{remote_path}': {error_output}")


__all__ = [
    "GenerationDestination",
    "build_remote_shell_path",
    "build_scp_remote_target",
    "format_remote_destination",
    "normalize_output_path",
    "prompt_generation_destination",
    "resolve_cli_destination",
    "resolve_remote_absolute_path",
    "resolve_remote_home_directory",
    "resolve_remote_upload_target",
    "write_rendered_files_remote",
]
