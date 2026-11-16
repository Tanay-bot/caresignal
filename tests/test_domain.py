from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from caresignal.comparison import build_comparison, compare_assistance
from caresignal.evidence import find_evidence, highlight_evidence, validate_evidence
from caresignal.models import (
    AssistanceLevel,
    EvidenceSpan,
    ExtractionResult,
    ExtractionRun,
    NoteRevision,
    ObservationCase,
    RunStatus,
    Target,
    UsualAssistance,
)

NOW = datetime(2026, 1, 10, tzinfo=timezone.utc)
DAY = date(2026, 1, 10)


def make_case(**changes):
    return ObservationCase(
        **dict(
            id="case",
            resident_id="elena",
            context_key="to_breakfast",
            observed_on=DAY,
            active_revision_id="rev-1",
            created_at=NOW,
        )
        | changes
    )


def make_run(label=AssistanceLevel.SUPERVISION, **changes):
    return ExtractionRun(
        **dict(
            id="run",
            revision_id="rev-1",
            extractor_mode="fixture",
            extractor_version="1",
            prompt_version="1",
            input_hash="hash",
            status=RunStatus.COMPLETE,
            created_at=NOW,
            result=ExtractionResult(
                label=label,
                reason_code="DOCUMENTED",
                reason="Documented in note.",
                evidence=[EvidenceSpan(revision_id="rev-1", start=0, end=4, quote="walk")],
            ),
        )
        | changes
    )


def make_baseline(level=AssistanceLevel.INDEPENDENT, **changes):
    return UsualAssistance(
        **dict(
            id="baseline",
            resident_id="elena",
            context_key="to_breakfast",
            level=level,
            source_description="Fictional staff confirmation.",
            confirmed_on=DAY,
            saved_at=NOW,
        )
        | changes
    )


@pytest.mark.parametrize(
    "observed,usual,expected",
    [
        (0, 0, "MATCHES"),
        (1, 1, "MATCHES"),
        (2, 2, "MATCHES"),
        (1, 0, "MORE_HELP"),
        (2, 1, "MORE_HELP"),
        (2, 0, "MORE_HELP"),
        (0, 1, "LESS_HELP"),
        (1, 2, "LESS_HELP"),
        (0, 2, "LESS_HELP"),
    ],
)
def test_rank_comparison(observed, usual, expected):
    assert compare_assistance(observed, usual) == expected


@pytest.mark.parametrize("observed,usual", [(-1, 1), (3, 0), (True, 0), (1, 1.0)])
def test_invalid_ranks_rejected(observed, usual):
    with pytest.raises(ValueError):
        compare_assistance(observed, usual)


def test_same_observation_can_have_different_comparisons():
    case = make_case()
    run = make_run()
    assert build_comparison(case, run, make_baseline()).status == "MORE_HELP"
    assert (
        build_comparison(case, run, make_baseline(AssistanceLevel.SUPERVISION)).status == "MATCHES"
    )
    assert (
        build_comparison(case, run, make_baseline(AssistanceLevel.HANDS_ON)).status == "LESS_HELP"
    )


@pytest.mark.parametrize(
    "baseline,reason",
    [
        (None, "NO_BASELINE"),
        (make_baseline(resident_id="ruth"), "BASELINE_RESIDENT_MISMATCH"),
        (make_baseline(context_key="from_breakfast"), "BASELINE_CONTEXT_MISMATCH"),
        (make_baseline(confirmed_on=date(2026, 1, 11)), "BASELINE_AFTER_OBSERVATION"),
    ],
)
def test_baseline_eligibility_preserves_extraction(baseline, reason):
    view = build_comparison(make_case(), make_run(), baseline)
    assert view.status == "UNCLEAR"
    assert view.reason_code == reason
    assert view.observed_label == AssistanceLevel.SUPERVISION
    assert view.baseline_id is None


@pytest.mark.parametrize("context", ["walking_attempt", "other_walk"])
def test_generic_context_never_upgraded_by_cue(context):
    view = build_comparison(
        make_case(context_key=context, target_cue="to breakfast"),
        make_run(),
        make_baseline(context_key=context),
    )
    assert view.status == "UNCLEAR"
    assert view.reason_code == "GENERIC_CONTEXT"


@pytest.mark.parametrize("label", [AssistanceLevel.HELP_UNSPECIFIED, AssistanceLevel.UNCLEAR])
def test_unspecified_labels_are_not_ranked(label):
    view = build_comparison(make_case(), make_run(label), make_baseline())
    assert view.status == "UNCLEAR"
    assert view.observed_label == label
    assert view.baseline_id is None


def test_stale_result_cannot_supply_current_card():
    view = build_comparison(make_case(active_revision_id="rev-2"), make_run(), make_baseline())
    assert view.reason_code == "STALE_EXTRACTION"
    assert view.observed_label is None
    assert view.extraction_id is None
    assert view.baseline_id is None
    assert view.revision_id == "rev-2"


@pytest.mark.parametrize("status", [RunStatus.UNAVAILABLE, RunStatus.INVALID])
def test_failed_run_distinct_from_valid_unclear(status):
    view = build_comparison(
        make_case(), make_run(status=status, result=None, error_category="timeout"), make_baseline()
    )
    assert view.status == "ANALYSIS_UNAVAILABLE"
    assert view.reason == "Retry the active note."
    assert view.reason_code == "timeout"
    assert view.observed_label is None


def test_not_analyzed_has_no_invented_extraction():
    view = build_comparison(make_case(), None, make_baseline())
    assert view.reason_code == "NOT_ANALYZED"
    assert view.observed_label is None


def test_adjacent_sentence_evidence_keeps_exact_original_text():
    body = "Ate well. She attempted to walk. The aide held her arm throughout. Later she rested."
    quote = "She attempted to walk. The aide held her arm throughout."
    span = find_evidence(body, "rev-1", quote)
    result = ExtractionResult(
        label=AssistanceLevel.HANDS_ON,
        reason_code="DOCUMENTED",
        reason="Physical support.",
        evidence=[span],
    )
    assert validate_evidence(body, "rev-1", result) is result
    assert body[span.start : span.end] == quote


@pytest.mark.parametrize("quote", ["", "absent", "walk"])
def test_missing_or_ambiguous_quote_rejected(quote):
    with pytest.raises(ValueError):
        find_evidence("walk and walk", "rev-1", quote)


@pytest.mark.parametrize(
    "span",
    [
        EvidenceSpan(revision_id="other", start=0, end=4, quote="walk"),
        EvidenceSpan(revision_id="rev-1", start=0, end=4, quote="Walk"),
        EvidenceSpan(revision_id="rev-1", start=0, end=20, quote="walk"),
    ],
)
def test_evidence_cannot_reference_other_revision_or_mismatched_text(span):
    result = ExtractionResult(
        label=AssistanceLevel.INDEPENDENT,
        reason_code="DOCUMENTED",
        reason="example",
        evidence=[span],
    )
    with pytest.raises(ValueError):
        validate_evidence("walk", "rev-1", result)


@pytest.mark.parametrize("label", list(AssistanceLevel))
def test_documented_levels_require_evidence(label):
    result = ExtractionResult(label=label, reason_code="NONE", reason="No source.")
    if label == AssistanceLevel.UNCLEAR:
        assert validate_evidence("walk", "rev-1", result) == result
    else:
        with pytest.raises(ValueError):
            validate_evidence("walk", "rev-1", result)


def test_highlighting_escapes_source_markup_and_merges_overlaps():
    body = '<script>alert("bad")</script> & walked beside her'
    span = find_evidence(body, "rev-1", "walked beside her")
    html = highlight_evidence(body, [span, span])
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&amp;" in html
    assert html.count("<mark>") == 1
    assert "<mark>walked beside her</mark>" in html


def test_models_reject_unknown_context_unspecific_baseline_and_mutation():
    with pytest.raises(ValidationError):
        Target(resident_id="elena", resident_name="Elena", context_key="lunch", observed_on=DAY)
    with pytest.raises(ValidationError):
        make_baseline(AssistanceLevel.HELP_UNSPECIFIED)
    with pytest.raises(ValidationError):
        make_baseline(source_description="  ")
    case = make_case()
    with pytest.raises(ValidationError):
        case.active_revision_id = "replacement"
    with pytest.raises(ValidationError):
        ObservationCase(**(case.model_dump() | {"invented": "field"}))


def test_invalid_status_payload_and_blank_note_rejected():
    with pytest.raises(ValidationError):
        make_run(result=None)
    with pytest.raises(ValidationError):
        make_run(status=RunStatus.UNAVAILABLE)
    with pytest.raises(ValidationError):
        NoteRevision(id="r", case_id="c", version=1, body=" \n ", created_at=NOW)


def test_run_cannot_carry_evidence_from_another_revision():
    with pytest.raises(ValidationError, match="Run evidence"):
        make_run(revision_id="rev-2")
