from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SCRIPT = REPO_ROOT / "scripts" / "install.sh"


def test_detect_os_does_not_override_install_version(tmp_path: Path) -> None:
    """Regression test for #1753 on Ubuntu 24.04 fresh installs."""
    os_release = tmp_path / "os-release"
    os_release.write_text(
        'ID=ubuntu\nVERSION_ID="24.04"\nVERSION="24.04.4 LTS (Noble Numbat)"\n',
        encoding="utf-8",
    )

    command = f"""
source "{INSTALL_SCRIPT}"
INSTALL_VERSION="latest"
VERSION="latest"
OSTYPE="linux-gnu"
OS_RELEASE_FILE="{os_release}"
detect_os
printf '%s\\n%s\\n%s\\n' "$INSTALL_VERSION" "$DISTRO_ID" "$DISTRO_VERSION"
"""

    result = subprocess.run(
        ["bash", "-lc", command],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["latest", "ubuntu", "24.04"]


def test_install_script_runs_from_stdin_with_nounset() -> None:
    """Regression test for stdin execution via `curl ... | bash`."""
    result = subprocess.run(
        ["bash", "-s", "--", "--help"],
        cwd=REPO_ROOT,
        input=INSTALL_SCRIPT.read_text(encoding="utf-8"),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Install the boilerplates CLI from GitHub releases via pipx." in result.stdout
