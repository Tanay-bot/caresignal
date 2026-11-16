"""Deterministic eligibility and wording for assistance comparisons."""

from caresignal.models import (
    COMPARABLE_CONTEXTS,
    LABELS,
    RANKS,
    AssistanceLevel,
    ComparisonView,
    ExtractionRun,
    ObservationCase,
    RunStatus,
    UsualAssistance,
)


def compare_assistance(observed_rank: int, usual_rank: int) -> str:
    """Order the three documentation categories, without clinical meaning."""
    if type(observed_rank) is not int or type(usual_rank) is not int:
        raise ValueError("Assistance ranks must be integers")
    if observed_rank not in range(3) or usual_rank not in range(3):
        raise ValueError("Assistance ranks must be between zero and two")
    if observed_rank > usual_rank:
        return "MORE_HELP"
    if observed_rank < usual_rank:
        return "LESS_HELP"
    return "MATCHES"


def build_comparison(
    case: ObservationCase,
    run: ExtractionRun | None,
    baseline: UsualAssistance | None,
) -> ComparisonView:
    """Build a view only from an active completed run and eligible baseline.

    The service validates evidence before saving a completed run and selects
    the latest eligible baseline. This function independently checks source,
    resident, context and date so callers cannot accidentally compare old data.
    """
    common = {"case_id": case.id, "revision_id": case.active_revision_id}

    def unclear(code: str, reason: str, **extra: object) -> ComparisonView:
        return ComparisonView(**common, status="UNCLEAR", reason_code=code, reason=reason, **extra)

    if run is None:
        return unclear("NOT_ANALYZED", "Analyze the active note to review documented help.")
    if run.revision_id != case.active_revision_id:
        return unclear("STALE_EXTRACTION", "The active note changed. Analyze the current revision.")
    if run.status != RunStatus.COMPLETE or run.result is None:
        return ComparisonView(
            **common,
            extraction_id=run.id,
            status="ANALYSIS_UNAVAILABLE",
            reason_code=run.error_category or run.status.value,
            reason="Retry the active note.",
        )

    observed = run.result.label
    extraction = {"extraction_id": run.id, "observed_label": observed}
    if observed == AssistanceLevel.HELP_UNSPECIFIED:
        return unclear(
            "HELP_TYPE_UNSPECIFIED",
            "The note describes help without specifying the level needed for a comparison.",
            **extraction,
        )
    if observed == AssistanceLevel.UNCLEAR:
        return unclear(run.result.reason_code, run.result.reason, **extraction)
    if case.context_key not in COMPARABLE_CONTEXTS:
        return unclear(
            "GENERIC_CONTEXT",
            "This walking context is not specific enough for a usual-level comparison.",
            **extraction,
        )
    if baseline is None:
        return unclear(
            "NO_BASELINE",
            "A usual level for this walk hasn’t been confirmed.",
            **extraction,
        )
    if baseline.resident_id != case.resident_id:
        return unclear(
            "BASELINE_RESIDENT_MISMATCH",
            "A usual level for this resident and walk hasn’t been confirmed.",
            **extraction,
        )
    if baseline.context_key != case.context_key:
        return unclear(
            "BASELINE_CONTEXT_MISMATCH",
            "A usual level for this walk hasn’t been confirmed.",
            **extraction,
        )
    if baseline.confirmed_on > case.observed_on:
        return unclear(
            "BASELINE_AFTER_OBSERVATION",
            "No usual level was confirmed by this observation date.",
            **extraction,
        )
    if baseline.level not in RANKS:
        return unclear(
            "BASELINE_UNSPECIFIED",
            "The usual level must specify a confirmed assistance category.",
            **extraction,
        )
    status = compare_assistance(RANKS[observed], RANKS[baseline.level])
    reason = (
        "Both sources show the same level for this walk."
        if status == "MATCHES"
        else f"Documented {LABELS[observed]}. Usual {LABELS[baseline.level]}."
    )
    return ComparisonView(
        **common,
        **extraction,
        baseline_id=baseline.id,
        status=status,
        reason_code="COMPARABLE_LEVELS",
        reason=reason,
    )
