"""Test for Traefik template to ensure no duplicate command arguments."""

import subprocess
import tempfile
from pathlib import Path


def test_traefik_no_duplicate_ping_entrypoint():
    """Test that the traefik template does not generate duplicate --ping.entryPoint arguments."""
    # Generate the template
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Run the CLI to generate the traefik template
        subprocess.run(
            [
                "python3",
                "-m",
                "cli",
                "compose",
                "generate",
                "traefik",
                "--no-interactive",
                "-o",
                str(output_dir),
                "--var",
                "traefik_tls_acme_email=test@example.com",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Read the generated compose.yaml
        compose_file = output_dir / "compose.yaml"
        assert compose_file.exists(), "compose.yaml not generated"

        content = compose_file.read_text()

        # Check for duplicate ping.entryPoint entries
        ping_entries = [line for line in content.split("\n") if "--ping.entryPoint=ping" in line]

        # Should have exactly one entry
        assert len(ping_entries) == 1, (
            f"Expected exactly 1 occurrence of '--ping.entryPoint=ping', "
            f"but found {len(ping_entries)}:\n" + "\n".join(ping_entries)
        )


def test_traefik_template_renders_successfully():
    """Test that the traefik template renders without errors."""
    # Generate the template
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Run the CLI to generate the traefik template
        subprocess.run(
            [
                "python3",
                "-m",
                "cli",
                "compose",
                "generate",
                "traefik",
                "--no-interactive",
                "-o",
                str(output_dir),
                "--var",
                "traefik_tls_acme_email=test@example.com",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Verify compose.yaml exists (main file)
        assert (output_dir / "compose.yaml").exists(), "compose.yaml not generated"
