"""Docker Compose validation functionality."""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from ...core.validation import KindValidationFailure, KindValidationResult

logger = logging.getLogger(__name__)


class ComposeDockerValidator:
    """Kind-specific validator backed by Docker Compose."""

    validator_name = "docker compose config"
    unavailable_message = "Required command is unavailable: docker compose"

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self._available: bool | None = None

    def is_available(self) -> bool:
        """Check whether Docker Compose is available locally."""
        if self._available is not None:
            return self._available

        if shutil.which("docker") is None:
            self._available = False
            return self._available

        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            check=False,
        )
        self._available = result.returncode == 0
        return self._available

    def validate_rendered_files(self, rendered_files: dict[str, str], _case_name: str) -> KindValidationResult:
        """Validate rendered Compose files with Docker Compose."""
        result = KindValidationResult(validator=self.validator_name, available=self.is_available())
        if not result.available:
            result.details.append(self.unavailable_message)
            return result

        compose_files = _find_compose_files(rendered_files)
        if not compose_files:
            result.warnings.append("No Docker Compose files found")
            return result

        for filename, content in compose_files:
            failure = self._validate_compose_content(filename, content)
            if failure is not None:
                result.failures.append(failure)

        return result

    def _validate_compose_content(self, filename: str, content: str) -> KindValidationFailure | None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            result = subprocess.run(
                ["docker", "compose", "-f", tmp_path, "config", "--quiet"],
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        if result.returncode == 0:
            return None

        message = result.stderr.strip() or result.stdout.strip() or "Docker Compose validation failed"
        return KindValidationFailure(file_path=filename, validator=self.validator_name, message=message)


def _find_compose_files(rendered_files: dict[str, str]) -> list[tuple[str, str]]:
    return [
        (filename, content)
        for filename, content in rendered_files.items()
        if filename.endswith(("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"))
    ]
