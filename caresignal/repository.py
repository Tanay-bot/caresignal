"""Workspace-scoped, transactional SQLite persistence for fictional handoffs."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterator
from uuid import uuid4

from .models import (
    AssistanceLevel,
    ExtractionRun,
    NoteRevision,
    ObservationCase,
    Resident,
    UsualAssistance,
)


class NotFoundError(LookupError):
    """The requested record does not exist in this workspace."""


class RevisionConflictError(RuntimeError):
    """The note changed after the caller selected the revision to replace."""


def _id() -> str:
    return uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS residents (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    display_name TEXT NOT NULL CHECK(length(trim(display_name)) > 0),
    is_demo INTEGER NOT NULL CHECK(is_demo IN (0, 1))
);
CREATE INDEX IF NOT EXISTS residents_workspace ON residents(workspace_id);
CREATE TABLE IF NOT EXISTS observation_cases (
    id TEXT PRIMARY KEY,
    resident_id TEXT NOT NULL REFERENCES residents(id) ON DELETE CASCADE,
    context_key TEXT NOT NULL CHECK(context_key IN (
        'to_breakfast','from_breakfast','hallway_walk','garden_walk','walking_attempt','other_walk')),
    observed_on TEXT NOT NULL,
    target_cue TEXT,
    active_revision_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(active_revision_id, id) REFERENCES note_revisions(id, case_id)
        DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS note_revisions (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES observation_cases(id) ON DELETE CASCADE,
    version INTEGER NOT NULL CHECK(version >= 1),
    body TEXT NOT NULL CHECK(length(trim(body)) > 0),
    created_at TEXT NOT NULL,
    supersedes_id TEXT,
    source_kind TEXT NOT NULL,
    source_note_id TEXT,
    UNIQUE(case_id, version),
    UNIQUE(id, case_id),
    FOREIGN KEY(supersedes_id, case_id) REFERENCES note_revisions(id, case_id)
        DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS usual_assistance (
    id TEXT PRIMARY KEY,
    resident_id TEXT NOT NULL REFERENCES residents(id) ON DELETE CASCADE,
    context_key TEXT NOT NULL CHECK(context_key IN (
        'to_breakfast','from_breakfast','hallway_walk','garden_walk','walking_attempt','other_walk')),
    level TEXT NOT NULL CHECK(level IN ('INDEPENDENT','SUPERVISION','HANDS_ON')),
    source_description TEXT NOT NULL CHECK(length(trim(source_description)) > 0),
    confirmed_on TEXT NOT NULL,
    saved_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS usual_lookup ON usual_assistance(
    resident_id, context_key, confirmed_on DESC, saved_at DESC);
CREATE TABLE IF NOT EXISTS extraction_runs (
    id TEXT PRIMARY KEY,
    revision_id TEXT NOT NULL REFERENCES note_revisions(id) ON DELETE CASCADE,
    extractor_mode TEXT NOT NULL,
    extractor_version TEXT NOT NULL,
    model_id TEXT,
    prompt_version TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('COMPLETE','UNAVAILABLE','INVALID')),
    result_json TEXT,
    error_category TEXT,
    created_at TEXT NOT NULL,
    CHECK((status = 'COMPLETE' AND result_json IS NOT NULL AND error_category IS NULL)
       OR (status != 'COMPLETE' AND result_json IS NULL AND error_category IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS runs_revision ON extraction_runs(revision_id, created_at DESC);
CREATE TRIGGER IF NOT EXISTS immutable_note_revision
BEFORE UPDATE ON note_revisions BEGIN
    SELECT RAISE(ABORT, 'note revisions are immutable');
END;
CREATE TRIGGER IF NOT EXISTS immutable_usual_assistance
BEFORE UPDATE ON usual_assistance BEGIN
    SELECT RAISE(ABORT, 'baseline snapshots are immutable');
END;
CREATE TRIGGER IF NOT EXISTS immutable_extraction_run
BEFORE UPDATE ON extraction_runs BEGIN
    SELECT RAISE(ABORT, 'extraction runs are immutable');
END;
CREATE TRIGGER IF NOT EXISTS stable_case_identity
BEFORE UPDATE OF resident_id, context_key, observed_on, target_cue, created_at ON observation_cases BEGIN
    SELECT RAISE(ABORT, 'observation identity is immutable');
END;
"""


class Repository:
    """Every record access is checked against the caller's workspace."""

    def __init__(self, db_path: str | Path):
        self.db_path = (
            str(Path(db_path).expanduser().resolve()) if str(db_path) != ":memory:" else ":memory:"
        )
        self._memory_uri: str | None = None
        self._anchor: sqlite3.Connection | None = None
        if self.db_path == ":memory:":
            # Keep a private shared-memory database alive across short connections.
            self._memory_uri = f"file:caresignal-{_id()}?mode=memory&cache=shared"
            self._anchor = self._connect()
        else:
            Path(self.db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.executescript(_SCHEMA)
            conn.execute("PRAGMA journal_mode = WAL")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self._memory_uri or self.db_path, uri=bool(self._memory_uri), timeout=10
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 10000")
        return conn

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _resident(self, conn: sqlite3.Connection, workspace_id: str, resident_id: str) -> Resident:
        row = conn.execute(
            "SELECT * FROM residents WHERE id = ? AND workspace_id = ?", (resident_id, workspace_id)
        ).fetchone()
        if row is None:
            raise NotFoundError("Resident not found in this workspace.")
        return Resident.model_validate(dict(row))

    def _case(self, conn: sqlite3.Connection, workspace_id: str, case_id: str) -> ObservationCase:
        row = conn.execute(
            """SELECT c.* FROM observation_cases c JOIN residents r ON r.id=c.resident_id
                              WHERE c.id = ? AND r.workspace_id = ?""",
            (case_id, workspace_id),
        ).fetchone()
        if row is None:
            raise NotFoundError("Observation not found in this workspace.")
        return ObservationCase.model_validate(dict(row))

    def _revision(self, conn: sqlite3.Connection, case_id: str, revision_id: str) -> NoteRevision:
        row = conn.execute(
            "SELECT * FROM note_revisions WHERE id = ? AND case_id = ?", (revision_id, case_id)
        ).fetchone()
        if row is None:
            raise NotFoundError("Revision does not belong to this observation.")
        return NoteRevision.model_validate(dict(row))

    def list_residents(self, workspace_id: str) -> list[Resident]:
        with self.connection() as conn:
            return [
                Resident.model_validate(dict(row))
                for row in conn.execute(
                    "SELECT * FROM residents WHERE workspace_id = ? ORDER BY display_name, id",
                    (workspace_id,),
                )
            ]

    def create_resident(
        self, workspace_id: str, display_name: str, is_demo: bool = True
    ) -> Resident:
        if not display_name.strip():
            raise ValueError("A fictional resident name is required.")
        resident = Resident(
            id=_id(), workspace_id=workspace_id, display_name=display_name, is_demo=is_demo
        )
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO residents VALUES (?, ?, ?, ?)",
                (resident.id, resident.workspace_id, resident.display_name, int(resident.is_demo)),
            )
        return resident

    def get_resident(self, workspace_id: str, resident_id: str) -> Resident:
        with self.connection() as conn:
            return self._resident(conn, workspace_id, resident_id)

    def list_cases(self, workspace_id: str, resident_id: str) -> list[ObservationCase]:
        with self.connection() as conn:
            self._resident(conn, workspace_id, resident_id)
            return [
                ObservationCase.model_validate(dict(row))
                for row in conn.execute(
                    """SELECT * FROM observation_cases WHERE resident_id = ?
                   ORDER BY observed_on DESC, created_at DESC, id""",
                    (resident_id,),
                )
            ]

    def get_case(self, workspace_id: str, case_id: str) -> ObservationCase:
        with self.connection() as conn:
            return self._case(conn, workspace_id, case_id)

    def get_revision(self, workspace_id: str, case_id: str, revision_id: str) -> NoteRevision:
        with self.connection() as conn:
            self._case(conn, workspace_id, case_id)
            return self._revision(conn, case_id, revision_id)

    def create_case(
        self,
        workspace_id: str,
        resident_id: str,
        context_key: str,
        observed_on: date,
        body: str,
        target_cue: str | None = None,
        source_kind: str = "custom",
        source_note_id: str | None = None,
    ) -> ObservationCase:
        case_id, revision_id, now = _id(), _id(), _now()
        case = ObservationCase(
            id=case_id,
            resident_id=resident_id,
            context_key=context_key,
            observed_on=observed_on,
            target_cue=target_cue,
            active_revision_id=revision_id,
            created_at=now,
        )
        revision = NoteRevision(
            id=revision_id,
            case_id=case_id,
            version=1,
            body=body,
            created_at=now,
            source_kind=source_kind,
            source_note_id=source_note_id,
        )
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._resident(conn, workspace_id, resident_id)
            conn.execute(
                "INSERT INTO observation_cases VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    case.id,
                    case.resident_id,
                    case.context_key,
                    case.observed_on.isoformat(),
                    case.target_cue,
                    case.active_revision_id,
                    case.created_at.isoformat(),
                ),
            )
            self._insert_revision(conn, revision)
        return case

    @staticmethod
    def _insert_revision(conn: sqlite3.Connection, revision: NoteRevision) -> None:
        conn.execute(
            "INSERT INTO note_revisions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                revision.id,
                revision.case_id,
                revision.version,
                revision.body,
                revision.created_at.isoformat(),
                revision.supersedes_id,
                revision.source_kind,
                revision.source_note_id,
            ),
        )

    def replace_active_revision(
        self, workspace_id: str, case_id: str, expected_revision_id: str, body: str
    ) -> NoteRevision:
        if not body.strip():
            raise ValueError("Replacement text is required.")
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            case = self._case(conn, workspace_id, case_id)
            if case.active_revision_id != expected_revision_id:
                raise RevisionConflictError(
                    "The active note changed. Review the latest note before replacing it."
                )
            original = self._revision(conn, case.id, expected_revision_id)
            revision = NoteRevision(
                id=_id(),
                case_id=case.id,
                version=original.version + 1,
                body=body,
                created_at=_now(),
                supersedes_id=original.id,
                source_kind="replacement",
            )
            self._insert_revision(conn, revision)
            cursor = conn.execute(
                """UPDATE observation_cases SET active_revision_id = ?
                                     WHERE id = ? AND active_revision_id = ?""",
                (revision.id, case.id, expected_revision_id),
            )
            if cursor.rowcount != 1:
                raise RevisionConflictError(
                    "The active note changed. Review the latest note before replacing it."
                )
        return revision

    def history(self, workspace_id: str, case_id: str) -> list[NoteRevision]:
        with self.connection() as conn:
            self._case(conn, workspace_id, case_id)
            return [
                NoteRevision.model_validate(dict(row))
                for row in conn.execute(
                    "SELECT * FROM note_revisions WHERE case_id = ? ORDER BY version DESC",
                    (case_id,),
                )
            ]

    def confirm_usual_assistance(
        self,
        workspace_id: str,
        resident_id: str,
        context_key: str,
        level: AssistanceLevel,
        source_description: str,
        confirmed_on: date,
    ) -> UsualAssistance:
        baseline = UsualAssistance(
            id=_id(),
            resident_id=resident_id,
            context_key=context_key,
            level=level,
            source_description=source_description,
            confirmed_on=confirmed_on,
            saved_at=_now(),
        )
        with self.connection() as conn:
            self._resident(conn, workspace_id, resident_id)
            conn.execute(
                "INSERT INTO usual_assistance VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    baseline.id,
                    baseline.resident_id,
                    baseline.context_key,
                    baseline.level.value,
                    baseline.source_description,
                    baseline.confirmed_on.isoformat(),
                    baseline.saved_at.isoformat(),
                ),
            )
        return baseline

    def _baseline(
        self, conn: sqlite3.Connection, resident_id: str, context_key: str, observed_on: date
    ) -> UsualAssistance | None:
        row = conn.execute(
            """SELECT * FROM usual_assistance WHERE resident_id = ? AND context_key = ?
                              AND confirmed_on <= ? ORDER BY confirmed_on DESC, saved_at DESC, rowid DESC LIMIT 1""",
            (resident_id, context_key, observed_on.isoformat()),
        ).fetchone()
        return UsualAssistance.model_validate(dict(row)) if row is not None else None

    def latest_baseline(
        self, workspace_id: str, resident_id: str, context_key: str, observed_on: date
    ) -> UsualAssistance | None:
        with self.connection() as conn:
            self._resident(conn, workspace_id, resident_id)
            return self._baseline(conn, resident_id, context_key, observed_on)

    def save_run(self, workspace_id: str, case_id: str, run: ExtractionRun) -> None:
        with self.connection() as conn:
            self._case(conn, workspace_id, case_id)
            self._revision(conn, case_id, run.revision_id)
            conn.execute(
                "INSERT INTO extraction_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run.id,
                    run.revision_id,
                    run.extractor_mode,
                    run.extractor_version,
                    run.model_id,
                    run.prompt_version,
                    run.input_hash,
                    run.status.value,
                    run.result.model_dump_json() if run.result else None,
                    run.error_category,
                    run.created_at.isoformat(),
                ),
            )

    @staticmethod
    def _latest_run(conn: sqlite3.Connection, revision_id: str) -> ExtractionRun | None:
        row = conn.execute(
            """SELECT * FROM extraction_runs WHERE revision_id = ?
                              ORDER BY created_at DESC, rowid DESC LIMIT 1""",
            (revision_id,),
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        from .models import ExtractionResult

        result_json = data.pop("result_json")
        data["result"] = ExtractionResult.model_validate_json(result_json) if result_json else None
        return ExtractionRun.model_validate(data)

    def handoff_snapshot(
        self, workspace_id: str, case_id: str
    ) -> tuple[
        ObservationCase, Resident, NoteRevision, ExtractionRun | None, UsualAssistance | None
    ]:
        # One read transaction prevents mixing fields from two simultaneous revisions.
        with self.connection() as conn:
            conn.execute("BEGIN")
            case = self._case(conn, workspace_id, case_id)
            resident = self._resident(conn, workspace_id, case.resident_id)
            revision = self._revision(conn, case.id, case.active_revision_id)
            run = self._latest_run(conn, revision.id)
            baseline = self._baseline(conn, resident.id, case.context_key, case.observed_on)
            return case, resident, revision, run, baseline

    def clear_workspace(self, workspace_id: str) -> None:
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM residents WHERE workspace_id = ?", (workspace_id,))
