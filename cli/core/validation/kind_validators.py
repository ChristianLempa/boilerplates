"""Kind-specific validators for rendered templates."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .validation_runner import KindValidationFailure, KindValidationResult


class RenderedFilesValidator:
    """Base class for validators that run CLI tools against rendered files."""

    validator_name: str
    unavailable_message: str

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self._available: bool | None = None

    def command_available(self, command: str) -> bool:
        return shutil.which(command) is not None

    def validate_rendered_files(self, rendered_files: dict[str, str], case_name: str) -> KindValidationResult:
        result = KindValidationResult(validator=self.validator_name, available=self.is_available())
        if not result.available:
            result.details.append(self.unavailable_message)
            return result

        with tempfile.TemporaryDirectory(prefix=f"boilerplates-{case_name[:20]}-") as tmp_dir:
            workdir = Path(tmp_dir)
            self._write_rendered_files(rendered_files, workdir)
            return self.validate_directory(workdir)

    def is_available(self) -> bool:
        raise NotImplementedError

    def validate_directory(self, workdir: Path) -> KindValidationResult:
        raise NotImplementedError

    @staticmethod
    def _write_rendered_files(rendered_files: dict[str, str], workdir: Path) -> None:
        for filename, content in rendered_files.items():
            path = workdir / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def run_command(
        self,
        args: list[str],
        workdir: Path,
        *,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=workdir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def failure_from_process(
        self,
        result: subprocess.CompletedProcess[str],
        file_path: str = "",
    ) -> KindValidationFailure | None:
        if result.returncode == 0:
            return None

        message = result.stderr.strip() or result.stdout.strip() or f"{self.validator_name} failed"
        return KindValidationFailure(file_path=file_path, validator=self.validator_name, message=message)


class TerraformValidator(RenderedFilesValidator):
    """Validate Terraform/OpenTofu configurations."""

    validator_name = "tofu validate"
    unavailable_message = "Required command is unavailable: tofu or terraform"

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(verbose)
        self.command = "tofu" if self.command_available("tofu") else "terraform"
        self.validator_name = f"{self.command} validate"

    def is_available(self) -> bool:
        if self._available is None:
            self._available = self.command_available(self.command)
        return self._available

    def validate_directory(self, workdir: Path) -> KindValidationResult:
        result = KindValidationResult(validator=self.validator_name)
        init = self.run_command([self.command, "init", "-backend=false", "-input=false", "-no-color"], workdir)
        failure = self.failure_from_process(init)
        if failure is not None:
            if self._is_provider_resolution_failure(failure.message):
                result.skipped = True
                result.warnings.append(failure.message)
            else:
                result.failures.append(failure)
            return result

        validate = self.run_command([self.command, "validate", "-no-color"], workdir)
        failure = self.failure_from_process(validate)
        if failure is not None:
            result.failures.append(failure)
        return result

    @staticmethod
    def _is_provider_resolution_failure(message: str) -> bool:
        return "Failed to resolve provider packages" in message or "could not connect to registry" in message


class KubernetesValidator(RenderedFilesValidator):
    """Validate Kubernetes manifests with kubectl client dry-run."""

    validator_name = "kubectl create --dry-run=client"
    unavailable_message = "Required command is unavailable: kubectl"

    def is_available(self) -> bool:
        if self._available is None:
            self._available = self.command_available("kubectl")
        return self._available

    def validate_directory(self, workdir: Path) -> KindValidationResult:
        result = KindValidationResult(validator=self.validator_name)
        process = self.run_command(["kubectl", "create", "--dry-run=client", "--validate=false", "-f", "."], workdir)
        failure = self.failure_from_process(process)
        if failure is not None:
            if self._is_cluster_discovery_failure(failure.message):
                result.skipped = True
                result.warnings.append(failure.message)
            else:
                result.failures.append(failure)
        return result

    @staticmethod
    def _is_cluster_discovery_failure(message: str) -> bool:
        return "couldn't get current server API group list" in message or "unable to recognize" in message


class HelmValidator(RenderedFilesValidator):
    """Validate Helm chart files."""

    validator_name = "helm lint"
    unavailable_message = "Required command is unavailable: helm"

    def is_available(self) -> bool:
        if self._available is None:
            self._available = self.command_available("helm")
        return self._available

    def validate_directory(self, workdir: Path) -> KindValidationResult:
        result = KindValidationResult(validator=self.validator_name)
        if not (workdir / "Chart.yaml").exists():
            result.skipped = True
            result.warnings.append("Rendered files do not include Chart.yaml")
            return result

        process = self.run_command(["helm", "lint", "."], workdir)
        failure = self.failure_from_process(process)
        if failure is not None:
            result.failures.append(failure)
        return result


class PackerValidator(RenderedFilesValidator):
    """Validate Packer templates."""

    validator_name = "packer validate"
    unavailable_message = "Required command is unavailable: packer"

    def is_available(self) -> bool:
        if self._available is None:
            self._available = self.command_available("packer")
        return self._available

    def validate_directory(self, workdir: Path) -> KindValidationResult:
        result = KindValidationResult(validator=self.validator_name)
        if list(workdir.glob("*.pkr.hcl")):
            target = "."
        else:
            candidates = sorted(path for path in workdir.rglob("*") if path.is_file() and path.suffix == ".json")
            if not candidates:
                result.skipped = True
                result.warnings.append("No Packer template files found")
                return result
            target = str(candidates[0].relative_to(workdir))

        process = self.run_command(["packer", "validate", target], workdir)
        failure = self.failure_from_process(process)
        if failure is not None:
            result.failures.append(failure)
        return result


class AnsibleValidator(RenderedFilesValidator):
    """Validate Ansible playbooks with syntax-check."""

    validator_name = "ansible-playbook --syntax-check"
    unavailable_message = "Required command is unavailable: ansible-playbook"

    def is_available(self) -> bool:
        if self._available is None:
            self._available = self.command_available("ansible-playbook")
        return self._available

    def validate_directory(self, workdir: Path) -> KindValidationResult:
        result = KindValidationResult(validator=self.validator_name)
        playbooks = self._find_playbooks(workdir)
        if not playbooks:
            result.skipped = True
            result.warnings.append("No Ansible playbooks found")
            return result

        env = os.environ.copy()
        env["ANSIBLE_LOCAL_TEMP"] = tempfile.mkdtemp(prefix="ansible-local-")
        env["ANSIBLE_REMOTE_TEMP"] = "/tmp/.ansible-${USER}/tmp"

        for playbook in playbooks:
            process = self.run_command(
                ["ansible-playbook", "--syntax-check", str(playbook.relative_to(workdir))],
                workdir,
                env=env,
            )
            failure = self.failure_from_process(process, str(playbook.relative_to(workdir)))
            if failure is not None:
                if self._is_dependency_resolution_failure(failure.message):
                    result.skipped = True
                    result.warnings.append(failure.message)
                    continue
                result.failures.append(failure)
        return result

    @staticmethod
    def _find_playbooks(workdir: Path) -> list[Path]:
        candidates = []
        for path in workdir.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".yaml", ".yml"}:
                continue
            if "playbook" in path.name.lower() or AnsibleValidator._looks_like_playbook(path):
                candidates.append(path)
        return candidates

    @staticmethod
    def _looks_like_playbook(path: Path) -> bool:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return False

        return any(line.lstrip().startswith("hosts:") for line in content.splitlines())

    @staticmethod
    def _is_dependency_resolution_failure(message: str) -> bool:
        return ("the role" in message and "was not found" in message) or "couldn't resolve module/action" in message
