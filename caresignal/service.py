"""Application operations shared by Streamlit, notebooks and tests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from .comparison import build_comparison
from .evidence import validate_evidence
from .models import (
    AssistanceLevel,
    ComparisonView,
    ExtractionResult,
    ExtractionRun,
    NoteRevision,
    ObservationCase,
    Resident,
    RunStatus,
    Target,
    UsualAssistance,
)
from .repository import NotFoundError as NotFoundError
from .repository import Repository
from .repository import RevisionConflictError as RevisionConflictError


class Extractor(Protocol):
    mode: str
    version: str
    model_id: str | None
    prompt_version: str

    def extract(self, note_body: str, target: Target, revision_id: str) -> ExtractionResult: ...


@dataclass(frozen=True)
class HandoffView:
    case: ObservationCase
    resident: Resident
    revision: NoteRevision
    run: ExtractionRun | None
    baseline: UsualAssistance | None
    comparison: ComparisonView


class CareSignalService:
    def __init__(self, db_path: str | Path, workspace_id: str):
        if not workspace_id.strip():
            raise ValueError("A workspace identifier is required.")
        self.workspace_id = workspace_id
        self.repository = Repository(db_path)

    def list_residents(self) -> list[Resident]:
        return self.repository.list_residents(self.workspace_id)

    def create_resident(self, display_name: str, is_demo: bool = True) -> Resident:
        return self.repository.create_resident(self.workspace_id, display_name, is_demo)

    def list_cases(self, resident_id: str) -> list[ObservationCase]:
        return self.repository.list_cases(self.workspace_id, resident_id)

    def create_case(
        self,
        resident_id: str,
        context_key: str,
        observed_on: date,
        body: str,
        target_cue: str | None = None,
        source_kind: str = "custom",
        source_note_id: str | None = None,
    ) -> ObservationCase:
        return self.repository.create_case(
            self.workspace_id,
            resident_id,
            context_key,
            observed_on,
            body,
            target_cue,
            source_kind,
            source_note_id,
        )

    def confirm_usual_assistance(
        self,
        resident_id: str,
        context_key: str,
        level: AssistanceLevel,
        source_description: str,
        confirmed_on: date,
    ) -> UsualAssistance:
        return self.repository.confirm_usual_assistance(
            self.workspace_id, resident_id, context_key, level, source_description, confirmed_on
        )

    def analyze_active_revision(self, case_id: str, extractor: Extractor) -> ExtractionRun:
        case, resident, revision, _, _ = self.repository.handoff_snapshot(
            self.workspace_id, case_id
        )
        target = Target(
            resident_id=resident.id,
            resident_name=resident.display_name,
            context_key=case.context_key,
            observed_on=case.observed_on,
            target_cue=case.target_cue,
        )
        input_hash = hashlib.sha256(
            json.dumps(
                {"body": revision.body, "target": target.model_dump(mode="json")},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        result: ExtractionResult | None = None
        error_category: str | None = None
        try:
            result = extractor.extract(revision.body, target, revision.id)
            if not isinstance(result, ExtractionResult):
                raise ValueError("Extractor did not return a validated result.")
            result = validate_evidence(revision.body, revision.id, result)
            status = RunStatus.COMPLETE
        except ValueError:
            # Includes schema errors and an exact span that does not resolve.
            status, result, error_category = RunStatus.INVALID, None, "invalid_output"
        except Exception as exc:
            # Provider details can contain request data. Store only a safe category.
            allowed = {
                "missing_credentials",
                "timeout",
                "rate_limit",
                "provider_error",
                "fixture_input_unsupported",
                "authentication",
                "connection_error",
                "refusal",
            }
            category = getattr(exc, "category", "provider_error")
            status, result = RunStatus.UNAVAILABLE, None
            error_category = category if category in allowed else "provider_error"
        run = ExtractionRun(
            id=uuid4().hex,
            revision_id=revision.id,
            extractor_mode=extractor.mode,
            extractor_version=extractor.version,
            model_id=extractor.model_id,
            prompt_version=extractor.prompt_version,
            input_hash=input_hash,
            status=status,
            result=result,
            error_category=error_category,
            created_at=datetime.now(timezone.utc),
        )
        # A correction can commit during inference. Its pointer is never changed here;
        # this result remains attached to exactly the revision requested above.
        self.repository.save_run(self.workspace_id, case.id, run)
        return run

    def replace_active_revision(
        self, case_id: str, expected_revision_id: str, body: str
    ) -> NoteRevision:
        return self.repository.replace_active_revision(
            self.workspace_id, case_id, expected_revision_id, body
        )

    def get_handoff_view(self, case_id: str) -> HandoffView:
        case, resident, revision, run, baseline = self.repository.handoff_snapshot(
            self.workspace_id, case_id
        )
        return HandoffView(
            case, resident, revision, run, baseline, build_comparison(case, run, baseline)
        )

    def history(self, case_id: str) -> list[NoteRevision]:
        return self.repository.history(self.workspace_id, case_id)

    def reset_demo(self) -> list[ObservationCase]:
        from .extractors import FixtureExtractor
        from .fixtures import DEMO_DATE, DEMO_NOTE

        self.repository.clear_workspace(self.workspace_id)
        cases = []
        for name, level, description in (
            ("Elena", AssistanceLevel.INDEPENDENT, "Usually walks to breakfast independently."),
            (
                "Ruth",
                AssistanceLevel.SUPERVISION,
                "Usually has an aide beside her for walking support on the way to breakfast.",
            ),
        ):
            resident = self.create_resident(name)
            self.confirm_usual_assistance(
                resident.id, "to_breakfast", level, description, DEMO_DATE
            )
            cases.append(
                self.create_case(
                    resident.id,
                    "to_breakfast",
                    DEMO_DATE,
                    DEMO_NOTE,
                    target_cue="outbound walk this morning",
                    source_kind="fixture",
                )
            )
        for case in cases:
            self.analyze_active_revision(case.id, FixtureExtractor())
        return cases
