"""The evidence history must survive replacement, failures and competing writes."""

import sqlite3
from datetime import date

import pytest

from caresignal.evidence import find_evidence
from caresignal.models import AssistanceLevel, ExtractionResult, RunStatus
from caresignal.repository import NotFoundError, Repository, RevisionConflictError
from caresignal.service import CareSignalService

DAY = date(2026, 1, 15)
NOTE = "She walked to breakfast. An aide stayed beside her for walking support."
REPLACEMENT = "She walked to breakfast with her walker."


class SupervisionExtractor:
    mode = "test"
    version = "test-v1"
    model_id = None
    prompt_version = "test-v1"

    def extract(self, note_body, target, revision_id):
        return ExtractionResult(
            label=AssistanceLevel.SUPERVISION,
            reason_code="EXPLICIT_SUPPORT",
            reason="Walking support is documented.",
            evidence=[find_evidence(note_body, revision_id, note_body)],
        )


class UnclearExtractor(SupervisionExtractor):
    def extract(self, note_body, target, revision_id):
        return ExtractionResult(
            label=AssistanceLevel.UNCLEAR,
            reason_code="DEVICE_ONLY",
            reason="The note mentions a walker. Human assistance is unspecified.",
            device="walker",
        )


class UnavailableExtractor(SupervisionExtractor):
    def extract(self, note_body, target, revision_id):
        raise RuntimeError("Provider error with sensitive details that must not be persisted")


@pytest.fixture
def service(tmp_path):
    return CareSignalService(tmp_path / "data" / "care.sqlite3", "workspace-a")


def make_case(service, body=NOTE, context="to_breakfast", baseline=AssistanceLevel.INDEPENDENT):
    resident = service.create_resident("Fictional Elena")
    case = service.create_case(resident.id, context, DAY, body)
    if baseline is not None:
        service.confirm_usual_assistance(
            resident.id,
            context,
            baseline,
            "Staff confirmed this selected level for this walk.",
            DAY,
        )
    return case


def test_two_fictional_residents_share_note_but_have_different_cards(service):
    first = make_case(service)
    second = make_case(service, baseline=AssistanceLevel.SUPERVISION)
    service.analyze_active_revision(first.id, SupervisionExtractor())
    service.analyze_active_revision(second.id, SupervisionExtractor())
    left, right = service.get_handoff_view(first.id), service.get_handoff_view(second.id)
    assert left.revision.body == right.revision.body
    assert left.comparison.status == "MORE_HELP"
    assert right.comparison.status == "MATCHES"
    assert left.comparison.baseline_id == left.baseline.id
    assert right.comparison.baseline_id == right.baseline.id


def test_replacement_clears_comparison_immediately_and_preserves_original(service):
    case = make_case(service)
    old_run = service.analyze_active_revision(case.id, SupervisionExtractor())
    replacement = service.replace_active_revision(case.id, case.active_revision_id, REPLACEMENT)
    pending = service.get_handoff_view(case.id)
    assert pending.revision.id == replacement.id
    assert pending.run is None
    assert pending.comparison.status != "MORE_HELP"
    assert pending.comparison.extraction_id is None
    new_run = service.analyze_active_revision(case.id, UnclearExtractor())
    current = service.get_handoff_view(case.id)
    assert current.comparison.status == "UNCLEAR"
    assert current.run.id == new_run.id != old_run.id
    assert current.run.result.evidence == []
    assert [(r.version, r.body) for r in service.history(case.id)] == [(2, REPLACEMENT), (1, NOTE)]
    assert replacement.supersedes_id == case.active_revision_id


def test_replacement_provider_error_never_resurrects_old_flag_or_evidence(service):
    case = make_case(service)
    service.analyze_active_revision(case.id, SupervisionExtractor())
    replacement = service.replace_active_revision(case.id, case.active_revision_id, REPLACEMENT)
    run = service.analyze_active_revision(case.id, UnavailableExtractor())
    view = service.get_handoff_view(case.id)
    assert view.revision.id == replacement.id
    assert run.status == RunStatus.UNAVAILABLE
    assert run.result is None
    assert run.error_category == "provider_error"
    assert view.comparison.status == "ANALYSIS_UNAVAILABLE"
    assert "sensitive" not in run.model_dump_json()


def test_stale_expected_revision_has_no_side_effect(service):
    case = make_case(service)
    second = service.replace_active_revision(case.id, case.active_revision_id, REPLACEMENT)
    with pytest.raises(RevisionConflictError):
        service.replace_active_revision(case.id, case.active_revision_id, "A stale correction.")
    assert service.get_handoff_view(case.id).revision.id == second.id
    assert len(service.history(case.id)) == 2


def test_failed_pointer_update_rolls_back_inserted_revision(service):
    case = make_case(service)
    with service.repository.connection() as conn:
        conn.executescript("""CREATE TRIGGER reject_pointer BEFORE UPDATE OF active_revision_id
                             ON observation_cases BEGIN SELECT RAISE(ABORT, 'simulated write failure'); END;""")
    with pytest.raises(sqlite3.IntegrityError):
        service.replace_active_revision(case.id, case.active_revision_id, REPLACEMENT)
    assert service.get_handoff_view(case.id).revision.id == case.active_revision_id
    assert len(service.history(case.id)) == 1


def test_result_finishing_after_correction_stays_on_historical_revision(service):
    case = make_case(service)

    class CorrectingExtractor(SupervisionExtractor):
        def extract(self, note_body, target, revision_id):
            service.replace_active_revision(case.id, revision_id, REPLACEMENT)
            return super().extract(note_body, target, revision_id)

    late_run = service.analyze_active_revision(case.id, CorrectingExtractor())
    view = service.get_handoff_view(case.id)
    assert late_run.revision_id == case.active_revision_id
    assert view.case.active_revision_id != late_run.revision_id
    assert view.run is None
    assert view.comparison.extraction_id is None
    assert view.comparison.status != "MORE_HELP"
    retried = service.analyze_active_revision(case.id, UnclearExtractor())
    assert retried.revision_id == view.revision.id
    assert retried.input_hash != late_run.input_hash
    assert len(service.history(case.id)) == 2


def test_workspace_isolation_covers_reads_writes_and_reset(service, tmp_path):
    case = make_case(service)
    outsider = CareSignalService(tmp_path / "data" / "care.sqlite3", "workspace-b")
    assert outsider.list_residents() == []
    with pytest.raises(NotFoundError):
        outsider.get_handoff_view(case.id)
    with pytest.raises(NotFoundError):
        outsider.history(case.id)
    with pytest.raises(NotFoundError):
        outsider.list_cases(case.resident_id)
    with pytest.raises(NotFoundError):
        outsider.create_case(case.resident_id, "to_breakfast", DAY, NOTE)
    with pytest.raises(NotFoundError):
        outsider.confirm_usual_assistance(
            case.resident_id, "to_breakfast", AssistanceLevel.INDEPENDENT, "A description.", DAY
        )
    with pytest.raises(NotFoundError):
        outsider.replace_active_revision(case.id, case.active_revision_id, REPLACEMENT)
    with pytest.raises(NotFoundError):
        outsider.analyze_active_revision(case.id, SupervisionExtractor())
    other_case = make_case(outsider)
    service.reset_demo()
    assert outsider.get_handoff_view(other_case.id).revision.body == NOTE
    assert len(service.list_residents()) == 2
    with pytest.raises(NotFoundError):
        service.get_handoff_view(case.id)


def test_historical_baseline_uses_confirmation_date_then_latest_saved(service):
    case = make_case(service, baseline=None)
    service.confirm_usual_assistance(
        case.resident_id,
        "to_breakfast",
        AssistanceLevel.HANDS_ON,
        "Older physical support.",
        date(2026, 1, 13),
    )
    service.confirm_usual_assistance(
        case.resident_id,
        "to_breakfast",
        AssistanceLevel.SUPERVISION,
        "First confirmation on observation date.",
        DAY,
    )
    chosen = service.confirm_usual_assistance(
        case.resident_id,
        "to_breakfast",
        AssistanceLevel.INDEPENDENT,
        "Updated confirmation on the same date.",
        DAY,
    )
    service.confirm_usual_assistance(
        case.resident_id,
        "to_breakfast",
        AssistanceLevel.HANDS_ON,
        "Future confirmation must not apply.",
        date(2026, 1, 16),
    )
    service.confirm_usual_assistance(
        case.resident_id,
        "from_breakfast",
        AssistanceLevel.HANDS_ON,
        "A different route must not apply.",
        DAY,
    )
    service.analyze_active_revision(case.id, SupervisionExtractor())
    view = service.get_handoff_view(case.id)
    assert view.baseline.id == chosen.id
    assert view.comparison.status == "MORE_HELP"


def test_baseline_change_recomputes_without_model_call(service):
    case = make_case(service)
    run = service.analyze_active_revision(case.id, SupervisionExtractor())
    assert service.get_handoff_view(case.id).comparison.status == "MORE_HELP"
    baseline = service.confirm_usual_assistance(
        case.resident_id,
        "to_breakfast",
        AssistanceLevel.HANDS_ON,
        "Usually receives physical support.",
        DAY,
    )
    view = service.get_handoff_view(case.id)
    assert view.run.id == run.id
    assert view.baseline.id == baseline.id
    assert view.comparison.status == "LESS_HELP"


def test_no_baseline_still_exposes_validated_extraction(service):
    case = make_case(service, baseline=None)
    service.analyze_active_revision(case.id, SupervisionExtractor())
    view = service.get_handoff_view(case.id)
    assert view.run.result.label == AssistanceLevel.SUPERVISION
    assert view.comparison.status == "UNCLEAR"
    assert view.baseline is None


def test_generic_walking_context_never_compares_even_with_baseline(service):
    case = make_case(service, context="walking_attempt")
    service.analyze_active_revision(case.id, SupervisionExtractor())
    assert service.get_handoff_view(case.id).comparison.status == "UNCLEAR"


def test_exact_source_text_is_preserved_and_blank_input_does_not_create_revision(service):
    body = "  A note with accented café text.\nA second line.  "
    case = make_case(service, body=body)
    assert service.get_handoff_view(case.id).revision.body == body
    with pytest.raises(ValueError):
        service.replace_active_revision(case.id, case.active_revision_id, "  \n ")
    assert len(service.history(case.id)) == 1


def test_invalid_exact_span_is_a_failed_run_not_a_valid_unclear_label(service):
    case = make_case(service)

    class InvalidExtractor(SupervisionExtractor):
        def extract(self, note_body, target, revision_id):
            result = super().extract(note_body, target, revision_id)
            wrong_span = result.evidence[0].model_copy(update={"revision_id": "another-revision"})
            return result.model_copy(update={"evidence": [wrong_span]})

    run = service.analyze_active_revision(case.id, InvalidExtractor())
    assert run.status == RunStatus.INVALID
    assert run.error_category == "invalid_output"
    assert run.result is None
    assert service.get_handoff_view(case.id).comparison.status == "ANALYSIS_UNAVAILABLE"


def test_sqlite_enforces_same_case_pointer_and_immutable_revisions(service):
    first = make_case(service)
    second = make_case(service)
    with pytest.raises(sqlite3.IntegrityError):
        with service.repository.connection() as conn:
            assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
            conn.execute(
                "UPDATE observation_cases SET active_revision_id = ? WHERE id = ?",
                (second.active_revision_id, first.id),
            )
    with pytest.raises(sqlite3.IntegrityError):
        with service.repository.connection() as conn:
            conn.execute(
                "UPDATE note_revisions SET body = ? WHERE id = ?",
                ("Mutated text", first.active_revision_id),
            )
    assert service.get_handoff_view(first.id).revision.body == NOTE


def test_in_memory_repository_supports_sequential_operations():
    repository = Repository(":memory:")
    resident = repository.create_resident("in-memory", "Fictional resident")
    assert repository.list_residents("in-memory") == [resident]


def test_reset_demo_populates_analyzed_cards(service):
    cases = service.reset_demo()
    assert len(cases) == 2
    views = [service.get_handoff_view(case.id) for case in cases]
    assert views[0].revision.body == views[1].revision.body
    assert {view.comparison.status for view in views} == {"MORE_HELP", "MATCHES"}


def test_database_path_expansion_is_used_for_connection(tmp_path, monkeypatch):
    from pathlib import Path

    original = Path.expanduser
    expected = tmp_path / "fictional-data" / "care.sqlite3"
    monkeypatch.setattr(
        Path,
        "expanduser",
        lambda path: expected if str(path) == "~/care.sqlite3" else original(path),
    )
    repository = Repository("~/care.sqlite3")
    resident = repository.create_resident("configured-path", "Fictional resident")
    assert repository.db_path == str(expected.resolve())
    assert expected.is_file()
    assert repository.list_residents("configured-path") == [resident]
