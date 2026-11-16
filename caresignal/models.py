"""Immutable contracts shared by storage, extraction, and the screen."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AssistanceLevel(str, Enum):
    INDEPENDENT = "INDEPENDENT"
    SUPERVISION = "SUPERVISION"
    HANDS_ON = "HANDS_ON"
    HELP_UNSPECIFIED = "HELP_UNSPECIFIED"
    UNCLEAR = "UNCLEAR"


class RunStatus(str, Enum):
    COMPLETE = "COMPLETE"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID = "INVALID"


CONTEXTS = {
    "to_breakfast": "To breakfast (outbound)",
    "from_breakfast": "From breakfast (return)",
    "hallway_walk": "Hallway walk",
    "garden_walk": "Garden walk",
    "walking_attempt": "Walking attempt",
    "other_walk": "Other walk",
}
COMPARABLE_CONTEXTS = frozenset({"to_breakfast", "from_breakfast", "hallway_walk", "garden_walk"})
LABELS = {
    AssistanceLevel.INDEPENDENT: "Independent",
    AssistanceLevel.SUPERVISION: "Staff beside or supervising",
    AssistanceLevel.HANDS_ON: "Hands-on help",
    AssistanceLevel.HELP_UNSPECIFIED: "Help documented, type unspecified",
    AssistanceLevel.UNCLEAR: "Unclear",
}
RANKS = {
    AssistanceLevel.INDEPENDENT: 0,
    AssistanceLevel.SUPERVISION: 1,
    AssistanceLevel.HANDS_ON: 2,
}


class Contract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Target(Contract):
    resident_id: str
    resident_name: str
    context_key: str
    observed_on: date
    target_cue: str | None = None

    @field_validator("context_key")
    @classmethod
    def known_context(cls, value: str) -> str:
        if value not in CONTEXTS:
            raise ValueError("Unknown walking context")
        return value


class Resident(Contract):
    id: str
    workspace_id: str
    display_name: str
    is_demo: bool = True


class ObservationCase(Contract):
    id: str
    resident_id: str
    context_key: str
    observed_on: date
    target_cue: str | None = None
    active_revision_id: str
    created_at: datetime

    @field_validator("context_key")
    @classmethod
    def known_context(cls, value: str) -> str:
        if value not in CONTEXTS:
            raise ValueError("Unknown walking context")
        return value


class NoteRevision(Contract):
    id: str
    case_id: str
    version: int = Field(ge=1)
    body: str
    created_at: datetime
    supersedes_id: str | None = None
    source_kind: str = "custom"
    source_note_id: str | None = None

    @field_validator("body")
    @classmethod
    def nonblank_body(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Note text cannot be blank")
        return value


class UsualAssistance(Contract):
    id: str
    resident_id: str
    context_key: str
    level: AssistanceLevel
    source_description: str
    confirmed_on: date
    saved_at: datetime

    @field_validator("context_key")
    @classmethod
    def known_context(cls, value: str) -> str:
        if value not in CONTEXTS:
            raise ValueError("Unknown walking context")
        return value

    @field_validator("level")
    @classmethod
    def specific_level(cls, value: AssistanceLevel) -> AssistanceLevel:
        if value not in RANKS:
            raise ValueError("A confirmed baseline requires a specific help level")
        return value

    @field_validator("source_description")
    @classmethod
    def nonblank_description(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("A baseline source description is required")
        return value


class EvidenceSpan(Contract):
    revision_id: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    quote: str = Field(min_length=1)

    @model_validator(mode="after")
    def nonempty_range(self) -> "EvidenceSpan":
        if self.end <= self.start:
            raise ValueError("Evidence range must be nonempty")
        return self


class ExtractionResult(Contract):
    label: AssistanceLevel
    reason_code: str
    reason: str
    evidence: list[EvidenceSpan] = Field(default_factory=list)
    device: str | None = None


class ExtractionRun(Contract):
    id: str
    revision_id: str
    extractor_mode: str
    extractor_version: str
    model_id: str | None = None
    prompt_version: str
    input_hash: str
    status: RunStatus
    result: ExtractionResult | None = None
    error_category: str | None = None
    created_at: datetime

    @model_validator(mode="after")
    def coherent_status(self) -> "ExtractionRun":
        if self.status == RunStatus.COMPLETE and self.result is None:
            raise ValueError("A complete run requires a result")
        if self.status != RunStatus.COMPLETE and self.result is not None:
            raise ValueError("An unsuccessful run cannot expose a result")
        if self.result is not None and any(
            span.revision_id != self.revision_id for span in self.result.evidence
        ):
            raise ValueError("Run evidence must belong to the run's note revision")
        return self


class ComparisonView(Contract):
    case_id: str
    revision_id: str
    extraction_id: str | None = None
    baseline_id: str | None = None
    status: str
    reason_code: str
    reason: str
    observed_label: AssistanceLevel | None = None
