"""Run template validation across dependency matrix cases."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..exceptions import TemplateRenderError, TemplateSyntaxError, TemplateValidationError
from ..validators import get_validator_registry

if TYPE_CHECKING:
    from cli.core.template import Template

    from .dependency_matrix import ValidationCase


@dataclass(frozen=True)
class ValidationFailure:
    """A failure from template, semantic, or kind-specific validation."""

    case_name: str
    stage: str
    message: str
    file_path: str = ""
    validator: str = ""


@dataclass(frozen=True)
class KindValidationFailure:
    """A kind-specific validation failure."""

    file_path: str
    message: str
    validator: str


@dataclass
class KindValidationResult:
    """Kind-specific validation result."""

    validator: str
    available: bool = True
    skipped: bool = False
    failures: list[KindValidationFailure] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.available and not self.failures


KindValidator = Callable[[dict[str, str], str], KindValidationResult]


@dataclass
class MatrixValidationSummary:
    """Aggregated validation results for a matrix run."""

    total_cases: int = 0
    failures: list[ValidationFailure] = field(default_factory=list)
    kind_available: bool = True
    kind_skipped_cases: set[str] = field(default_factory=set)

    @property
    def ok(self) -> bool:
        return not self.failures


class ValidationRunner:
    """Render validation cases and run semantic and optional kind validation."""

    def __init__(
        self,
        template: Template,
        cases: list[ValidationCase],
        *,
        semantic: bool = True,
        kind_validator: KindValidator | None = None,
    ) -> None:
        self.template = template
        self.cases = cases
        self.semantic = semantic
        self.kind_validator = kind_validator

    def run(self) -> MatrixValidationSummary:
        summary = MatrixValidationSummary(total_cases=len(self.cases))

        for case in self.cases:
            try:
                rendered_files, _ = self.template.render(case.variables)
            except (TemplateRenderError, TemplateSyntaxError, TemplateValidationError, ValueError) as exc:
                summary.failures.append(ValidationFailure(case_name=case.name, stage="tpl", message=str(exc)))
                continue

            if self.semantic:
                self._run_semantic(case.name, rendered_files, summary)

            if self.kind_validator is not None:
                self._run_kind(case.name, rendered_files, summary)

        return summary

    def _run_semantic(
        self,
        case_name: str,
        rendered_files: dict[str, str],
        summary: MatrixValidationSummary,
    ) -> None:
        registry = get_validator_registry()

        for file_path, content in rendered_files.items():
            result = registry.validate_file(content, file_path)
            for error in result.errors:
                validator = registry.get_validator(file_path)
                summary.failures.append(
                    ValidationFailure(
                        case_name=case_name,
                        stage="sem",
                        file_path=file_path,
                        validator=validator.__class__.__name__ if validator else "semantic",
                        message=error,
                    )
                )

    def _run_kind(
        self,
        case_name: str,
        rendered_files: dict[str, str],
        summary: MatrixValidationSummary,
    ) -> None:
        result = self.kind_validator(rendered_files, case_name)
        summary.kind_available = summary.kind_available and result.available

        if not result.available:
            summary.kind_skipped_cases.add(case_name)
            return

        if result.skipped:
            summary.kind_skipped_cases.add(case_name)
            return

        for failure in result.failures:
            summary.failures.append(
                ValidationFailure(
                    case_name=case_name,
                    stage="kind",
                    file_path=failure.file_path,
                    validator=failure.validator,
                    message=failure.message,
                )
            )
