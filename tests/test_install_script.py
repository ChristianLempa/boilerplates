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
    assert "Install the boilerplates CLI from GitHub releases via uv or pipx." in result.stdout
    assert "--macos-installer VAL" in result.stdout
    assert "--linux-installer VAL" in result.stdout


def test_parse_args_accepts_platform_installer_flags() -> None:
    command = f'''
source "{INSTALL_SCRIPT}"
parse_args --macos-installer uv --linux-installer pipx
printf '%s\n%s\n' "$MACOS_DEPENDENCY_INSTALLER" "$LINUX_DEPENDENCY_INSTALLER"
'''

    result = subprocess.run(
        ["bash", "-lc", command],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["uv", "pipx"]


def test_check_dependencies_accepts_uv_without_pipx(tmp_path: Path) -> None:
    """uv should satisfy installer requirements when pipx is absent."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()

    python3_script = fake_bin / "python3"
    python3_script.write_text(
        "#!/usr/bin/env bash\n"
        "if [[ \"$1\" == \"-m\" && \"$2\" == \"pip\" && \"$3\" == \"--version\" ]]; then\n"
        "  echo 'pip 24.0'\n"
        "  exit 0\n"
        "fi\n"
        "if [[ \"$1\" == \"-m\" && \"$2\" == \"site\" && \"$3\" == \"--user-base\" ]]; then\n"
        "  echo '/nonexistent'\n"
        "  exit 0\n"
        "fi\n"
        "exit 1\n",
        encoding="utf-8",
    )
    python3_script.chmod(0o755)

    git_script = fake_bin / "git"
    git_script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    git_script.chmod(0o755)

    uv_script = fake_bin / "uv"
    uv_script.write_text(
        "#!/usr/bin/env bash\n"
        "if [[ \"$1\" == \"--version\" ]]; then\n"
        "  echo 'uv 0.5.0'\n"
        "  exit 0\n"
        "fi\n"
        "exit 1\n",
        encoding="utf-8",
    )
    uv_script.chmod(0o755)

    command = f'''
source "{INSTALL_SCRIPT}"
PATH="{fake_bin}:$PATH"
AUTO_INSTALL=false
check_dependencies
printf '%s\n' "$INSTALL_METHOD"
'''

    result = subprocess.run(
        ["bash", "-lc", command],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[-1] == "uv"


def test_check_dependencies_accepts_pipx_without_uv(tmp_path: Path) -> None:
    """pipx should satisfy installer requirements when uv is absent."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()

    python3_script = fake_bin / "python3"
    python3_script.write_text(
        "#!/usr/bin/env bash\n"
        "if [[ \"$1\" == \"-m\" && \"$2\" == \"site\" && \"$3\" == \"--user-base\" ]]; then\n"
        "  echo '/nonexistent'\n"
        "  exit 0\n"
        "fi\n"
        "exit 1\n",
        encoding="utf-8",
    )
    python3_script.chmod(0o755)

    git_script = fake_bin / "git"
    git_script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    git_script.chmod(0o755)

    uv_script = fake_bin / "uv"
    uv_script.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    uv_script.chmod(0o755)

    uvx_script = fake_bin / "uvx"
    uvx_script.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    uvx_script.chmod(0o755)

    pipx_script = fake_bin / "pipx"
    pipx_script.write_text(
        "#!/usr/bin/env bash\n"
        "if [[ \"$1\" == \"--version\" ]]; then\n"
        "  echo '1.7.1'\n"
        "  exit 0\n"
        "fi\n"
        "exit 1\n",
        encoding="utf-8",
    )
    pipx_script.chmod(0o755)

    command = f'''
source "{INSTALL_SCRIPT}"
PATH="{fake_bin}:$PATH"
AUTO_INSTALL=false
check_dependencies
printf '%s\n' "$INSTALL_METHOD"
'''

    result = subprocess.run(
        ["bash", "-lc", command],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[-1] == "pipx"


def test_check_dependencies_rejects_standalone_uvx_without_uv(tmp_path: Path) -> None:
    """A standalone uvx should not satisfy uv availability without a sibling uv binary."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()

    git_script = fake_bin / "git"
    git_script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    git_script.chmod(0o755)

    uv_script = fake_bin / "uv"
    uv_script.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    uv_script.chmod(0o755)

    uvx_script = fake_bin / "uvx"
    uvx_script.write_text(
        "#!/usr/bin/env bash\n"
        "if [[ \"$1\" == \"--version\" ]]; then\n"
        "  echo 'uvx 0.5.0'\n"
        "  exit 0\n"
        "fi\n"
        "exit 1\n",
        encoding="utf-8",
    )
    uvx_script.chmod(0o755)

    pipx_script = fake_bin / "pipx"
    pipx_script.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    pipx_script.chmod(0o755)

    command = f'''
source "{INSTALL_SCRIPT}"
PATH="{fake_bin}:$PATH"
AUTO_INSTALL=false
check_dependencies
'''

    result = subprocess.run(
        ["bash", "-lc", command],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Missing dependencies. Install: git and uv or pipx" in result.stderr
