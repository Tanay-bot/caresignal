"""Validate source citations and render escaped evidence safely."""

from html import escape
from typing import Iterable

from caresignal.models import AssistanceLevel, EvidenceSpan, ExtractionResult


def _check_span(body: str, revision_id: str, span: EvidenceSpan) -> None:
    if span.revision_id != revision_id:
        raise ValueError("Evidence belongs to a different note revision")
    if not 0 <= span.start < span.end <= len(body):
        raise ValueError("Evidence indices are outside the source note")
    if body[span.start : span.end] != span.quote:
        raise ValueError("Evidence quote does not match the exact source text")


def validate_evidence(
    note_body: str, revision_id: str, result: ExtractionResult
) -> ExtractionResult:
    """Return a validated result or fail closed on unsupported citations.

    This verifies citation integrity; whether a quote semantically supports its
    label is evaluated separately against annotated examples.
    """
    if result.label != AssistanceLevel.UNCLEAR and not result.evidence:
        raise ValueError("A documented assistance label requires exact evidence")
    for span in result.evidence:
        _check_span(note_body, revision_id, span)
    return result


def find_evidence(note_body: str, revision_id: str, quote: str) -> EvidenceSpan:
    """Resolve a verbatim unique quote to half-open Python string offsets."""
    if not quote:
        raise ValueError("An evidence quote cannot be empty")
    start = note_body.find(quote)
    if start < 0:
        raise ValueError("Evidence quote was not found in the source note")
    if note_body.find(quote, start + 1) >= 0:
        raise ValueError("Evidence quote is ambiguous; use a longer unique quote")
    return EvidenceSpan(revision_id=revision_id, start=start, end=start + len(quote), quote=quote)


def highlight_evidence(body: str, spans: Iterable[EvidenceSpan]) -> str:
    """Escape all source text before adding controlled highlight markup.

    Overlapping or adjacent valid spans are merged to keep markup well formed.
    Revision checks belong to validate_evidence; this function also verifies
    every range against the supplied text before rendering it.
    """
    ranges: list[tuple[int, int]] = []
    for span in spans:
        _check_span(body, span.revision_id, span)
        ranges.append((span.start, span.end))
    merged: list[list[int]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    cursor = 0
    chunks: list[str] = []
    for start, end in merged:
        chunks.append(escape(body[cursor:start]))
        chunks.append("<mark>" + escape(body[start:end]) + "</mark>")
        cursor = end
    chunks.append(escape(body[cursor:]))
    return "".join(chunks)
