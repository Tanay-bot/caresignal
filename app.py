"""CareSignal's fictional, evidence-first Streamlit handoff workspace."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from pathlib import Path
from uuid import uuid4

import streamlit as st

from caresignal.evidence import highlight_evidence
from caresignal.extractors import FixtureExtractor, OpenAIExtractor, PhraseMatcher
from caresignal.fixtures import DEMO_DATE, DEMO_NOTE, DEMO_REPLACEMENT
from caresignal.models import CONTEXTS, LABELS, AssistanceLevel, RunStatus
from caresignal.service import CareSignalService, RevisionConflictError

FRUTA_PRESET = Path(__file__).resolve().parent / "data" / "fruta_nn_1093.json"


def _fruta_example() -> dict:
    return json.loads(FRUTA_PRESET.read_text(encoding="utf-8"))


st.set_page_config(page_title="CareSignal", page_icon="🌿", layout="wide")
st.markdown(
    """
    <style>
    :root { color-scheme: light; }
    .stApp { background: #f7faf9; }
    .block-container { max-width: 1220px; padding-top: 2rem; }
    h1, h2, h3 { color: #163d3a; letter-spacing: -.025em; }
    div[data-testid="stMetricValue"] { color: #163d3a; }
    .source-note { white-space: pre-wrap; line-height: 1.7; color: #193f3b; }
    mark { background: #ffe6a0; color: #172d29; padding: .06rem .12rem; }
    div[data-testid="stSidebar"] { background: #eaf2f0; }
    button[kind="primary"] { background-color: #176c63; border-color: #176c63; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _make_service() -> CareSignalService:
    if "workspace_id" not in st.session_state:
        st.session_state.workspace_id = str(uuid4())
    data_dir = Path(
        os.environ.get("CARESIGNAL_DATA_DIR", str(Path(tempfile.gettempdir()) / "caresignal"))
    )
    data_dir.mkdir(parents=True, exist_ok=True)
    return CareSignalService(data_dir / "history.sqlite3", st.session_state.workspace_id)


def _extractor(mode: str):
    return {
        "Fixture demo": FixtureExtractor,
        "Phrase matcher": PhraseMatcher,
        "Live AI": OpenAIExtractor,
    }[mode]()


def _analyze(service: CareSignalService, case_id: str, mode: str) -> None:
    service.analyze_active_revision(case_id, _extractor(mode))


def _result(view, mode: str) -> bool:
    """Render only data belonging to the selected active source."""
    run = view.run
    result = run.result if run and run.status == RunStatus.COMPLETE else None
    comparison = view.comparison
    headlines = {
        "MORE_HELP": "↑ More help than usual",
        "LESS_HELP": "↓ Less help than usual",
        "MATCHES": "✓ Matches usual routine",
    }
    with st.container(border=True):
        st.caption(f"HANDOFF RESULT · ACTIVE SOURCE V{view.revision.version}")
        if comparison.status in headlines:
            st.subheader(headlines[comparison.status])
        elif result:
            st.subheader(LABELS[result.label])
        else:
            st.subheader("Analysis unavailable" if run else "Ready to analyze")
        if result:
            st.markdown(f"**Documented help:** {LABELS[result.label]}")
            if view.baseline:
                st.markdown(f"**Usual help:** {LABELS[view.baseline.level]}")
            st.write(comparison.reason)
            if result.reason and result.reason != comparison.reason:
                st.caption(result.reason)
            if result.device:
                st.caption(f"Device mentioned: {result.device}")
        else:
            st.write(
                "Retry the active note."
                if run
                else "Analyze this note to review documented walking help."
            )
            if run and run.error_category:
                st.caption(f"Error category: {run.error_category}")
        if run:
            st.caption(
                f"Analysis mode: {run.extractor_mode} · source version {view.revision.version}"
                + (f" · model {run.model_id}" if run.model_id else "")
            )
        retry = st.button(
            "Retry active note"
            if run and run.status != RunStatus.COMPLETE
            else "Analyze active note",
            key=f"retry_{view.case.id}_{view.revision.id}",
            help=f"Analyze source version {view.revision.version} using {mode}.",
        )

    with st.expander("View evidence", expanded=True):
        st.markdown("**Active shift note**")
        st.caption(
            f"{view.case.observed_on.isoformat()} · version {view.revision.version} · "
            f"{view.revision.source_kind}"
        )
        if view.revision.source_note_id:
            st.caption(f"Source note ID: {view.revision.source_note_id}")
        spans = result.evidence if result else []
        st.markdown(
            f'<div class="source-note">{highlight_evidence(view.revision.body, spans)}</div>',
            unsafe_allow_html=True,
        )
        if view.revision.source_kind == "fruta" and view.revision.source_note_id == "nn_1093":
            source = _fruta_example()
            if view.revision.body == source["note"]:
                st.caption(
                    f"Fruta development example · dataset revision {source['dataset_revision'][:12]} · "
                    f"translation {source['translation_id']}"
                )
                st.markdown(f"[Frozen public source]({source['source_url']})")
                with st.expander("Original Dutch text"):
                    st.text(source["original_note"])
                    st.caption(source["translation_method"])
        if result and not spans:
            st.caption("No usable evidence of human assistance was identified in this active note.")
        st.divider()
        st.markdown("**Staff-confirmed usual assistance**")
        if view.baseline:
            st.write(LABELS[view.baseline.level])
            st.write(view.baseline.source_description)
            st.caption(
                f"Confirmed {view.baseline.confirmed_on.isoformat()} · "
                f"{CONTEXTS[view.baseline.context_key]}"
            )
        else:
            st.caption("A usual level for this walk hasn’t been confirmed.")
    return retry


def _new_note(service: CareSignalService, resident, view, mode: str) -> None:
    with st.expander("Analyze a new note", expanded=True):
        st.caption("Create a separate observation for one selected walk. Use fictional notes only.")
        with st.form(f"new_note_{resident.id}"):
            context = st.selectbox(
                "Target walk",
                list(CONTEXTS),
                index=list(CONTEXTS).index(view.case.context_key) if view else 0,
                format_func=CONTEXTS.get,
                key=f"new_context_{resident.id}",
            )
            observed = st.date_input(
                "Observation date",
                value=view.case.observed_on if view else DEMO_DATE,
                key=f"new_date_{resident.id}",
            )
            cue = st.text_input(
                "Target cue (optional)",
                placeholder="For example, outbound walk this morning",
                key=f"new_cue_{resident.id}",
            )
            body = st.text_area(
                "Complete shift note",
                value=DEMO_NOTE,
                height=160,
                key=f"new_body_{resident.id}",
            )
            submitted = st.form_submit_button("Analyze note", type="primary")
            if submitted:
                if not body.strip():
                    st.error("Enter the complete note before analyzing it.")
                else:
                    try:
                        case = service.create_case(
                            resident.id, context, observed, body, target_cue=cue or None
                        )
                        with st.spinner("Analyzing the selected walk…"):
                            _analyze(service, case.id, mode)
                        st.session_state.next_case_id = case.id
                        st.rerun()
                    except ValueError:
                        st.error("Check the note, date and target walk, then try again.")


def _baseline(service: CareSignalService, view) -> None:
    case = view.case
    draft_key = f"baseline_draft_{case.id}"
    with st.expander("Set usual assistance"):
        st.caption(f"{view.resident.display_name} · {CONTEXTS[case.context_key]}")
        with st.form(f"baseline_{case.id}"):
            level = st.selectbox(
                "Specific usual help level",
                [
                    AssistanceLevel.INDEPENDENT,
                    AssistanceLevel.SUPERVISION,
                    AssistanceLevel.HANDS_ON,
                ],
                format_func=LABELS.get,
                key=f"baseline_level_{case.id}",
            )
            description = st.text_area(
                "Staff-confirmed source description",
                key=f"baseline_description_{case.id}",
                placeholder="Describe the usual human help for this walk.",
            )
            confirmed_on = st.date_input(
                "Confirmation date", value=case.observed_on, key=f"baseline_date_{case.id}"
            )
            if st.form_submit_button("Review usual assistance"):
                if not description.strip():
                    st.error("Add a source description before confirming usual assistance.")
                else:
                    st.session_state[f"baseline_agrees_{case.id}"] = False
                    st.session_state[draft_key] = {
                        "level": level,
                        "description": description,
                        "confirmed_on": confirmed_on,
                    }
        draft = st.session_state.get(draft_key)
        if draft:
            st.markdown("**Check both values before confirming**")
            st.write(f"Usual help: {LABELS[draft['level']]}")
            st.write(f"Source description: {draft['description']}")
            st.caption(f"Confirmation date: {draft['confirmed_on'].isoformat()}")
            agrees = st.checkbox(
                "I confirm this level and description agree.",
                key=f"baseline_agrees_{case.id}",
            )
            if st.button("Confirm usual assistance", disabled=not agrees, key=f"confirm_{case.id}"):
                try:
                    service.confirm_usual_assistance(
                        case.resident_id,
                        case.context_key,
                        draft["level"],
                        draft["description"],
                        draft["confirmed_on"],
                    )
                    st.session_state.pop(draft_key, None)
                    st.rerun()
                except ValueError:
                    st.error("Check the usual level and confirmation details, then try again.")


def _replacement(service: CareSignalService, view, mode: str, result_area) -> None:
    revision = view.revision
    key = f"replacement_body_{view.case.id}_{revision.id}"
    with st.expander("Attach replacement"):
        st.caption(f"Replacing active note version {revision.version}")
        st.text(revision.body)
        st.info(
            "This replacement becomes the source for the current card. "
            "The previous note stays in history."
        )
        if st.button("Use demo replacement", key=f"use_replacement_{revision.id}"):
            st.session_state[key] = DEMO_REPLACEMENT
        with st.form(f"replacement_{revision.id}"):
            body = st.text_area("Full replacement note", height=130, key=key)
            if st.form_submit_button("Attach replacement", type="primary"):
                if not body.strip():
                    st.error("Enter a nonblank replacement note. Your draft has been kept.")
                else:
                    try:
                        service.replace_active_revision(view.case.id, revision.id, body)
                        result_area.empty()
                        with result_area.container():
                            st.info("Analyzing replacement…")
                        _analyze(service, view.case.id, mode)
                        st.rerun()
                    except RevisionConflictError:
                        latest = service.get_handoff_view(view.case.id)
                        st.session_state[
                            f"replacement_body_{view.case.id}_{latest.revision.id}"
                        ] = body
                        st.session_state.conflict_notice = (
                            "The active source changed. Review the latest note before attaching "
                            "your replacement. Your draft has been kept."
                        )
                        st.rerun()
                    except ValueError:
                        st.error(
                            "The replacement is invalid. Check the note and retry. Your draft has been kept."
                        )


def main() -> None:
    service = _make_service()
    if not st.session_state.get("demo_initialized"):
        service.reset_demo()
        st.session_state.demo_initialized = True

    with st.sidebar:
        st.markdown("### Review workspace")
        mode = st.radio("Extractor mode", ["Fixture demo", "Phrase matcher", "Live AI"])
        if mode == "Fixture demo":
            st.caption(
                "Fixed fictional examples. Arbitrary notes require Live AI or the phrase matcher."
            )
        elif mode == "Phrase matcher":
            st.caption(
                "A conservative phrase baseline. Ambiguous event attribution produces Unclear."
            )
        else:
            st.caption("Structured extraction using the configured OpenAI model.")
            if not os.environ.get("OPENAI_API_KEY"):
                st.info(
                    "Set OPENAI_API_KEY to enable live extraction. The demo still works offline."
                )
        st.divider()
        st.caption("PUBLIC SYNTHETIC DEVELOPMENT EXAMPLE")
        if st.button("Load Fruta example", use_container_width=True):
            source = _fruta_example()
            target = source["target"]
            source_resident = next(
                (
                    item
                    for item in service.list_residents()
                    if item.display_name == target["resident_name"]
                ),
                None,
            )
            if source_resident is None:
                source_resident = service.create_resident(target["resident_name"], is_demo=True)
            case = service.create_case(
                source_resident.id,
                target["context_key"],
                date.fromisoformat(target["observed_on"]),
                source["note"],
                target_cue=target["target_cue"],
                source_kind="fruta",
                source_note_id=source["note_id"],
            )
            with st.spinner("Analyzing Fruta development example…"):
                _analyze(service, case.id, mode)
            st.session_state.resident_id = source_resident.id
            st.session_state.last_resident_id = source_resident.id
            st.session_state.next_case_id = case.id
            st.rerun()
        st.caption(
            "nn_1093 · Dutch original and frozen English translation. Uses the selected extractor."
        )
        st.divider()
        st.caption(
            "Fictional residents only. Each browser session has an isolated demo workspace in a local SQLite database. A new session starts a fresh workspace."
        )

    title, controls = st.columns([4, 1])
    with title:
        st.title("CareSignal")
        st.caption(f"Walking assistance, grounded in the note · {mode}")
    with controls:
        st.write("")
        if st.button("Load demo", use_container_width=True):
            service.reset_demo()
            for key in ("resident_id", "case_id", "last_resident_id", "next_case_id"):
                st.session_state.pop(key, None)
            st.rerun()

    if notice := st.session_state.pop("conflict_notice", None):
        st.warning(notice)

    residents = service.list_residents()
    residents = sorted(residents, key=lambda item: item.display_name)
    resident_by_id = {resident.id: resident for resident in residents}
    context_columns = st.columns([1, 2])
    with context_columns[0]:
        resident_id = st.selectbox(
            "Fictional resident",
            list(resident_by_id),
            format_func=lambda value: resident_by_id[value].display_name,
            key="resident_id",
        )
    resident = resident_by_id[resident_id]
    if st.session_state.get("last_resident_id") != resident_id:
        st.session_state.pop("case_id", None)
        st.session_state.pop("next_case_id", None)
        st.session_state.last_resident_id = resident_id

    cases = sorted(service.list_cases(resident_id), key=lambda case: case.created_at, reverse=True)
    case_by_id = {case.id: case for case in cases}
    next_case_id = st.session_state.pop("next_case_id", None)
    if next_case_id in case_by_id:
        st.session_state.case_id = next_case_id
    if st.session_state.get("case_id") not in case_by_id:
        st.session_state.pop("case_id", None)
    with context_columns[1]:
        case_id = st.selectbox(
            "Observation",
            list(case_by_id),
            format_func=lambda value: (
                f"{CONTEXTS[case_by_id[value].context_key]} · {case_by_id[value].observed_on.isoformat()}"
                + (f" · {case_by_id[value].target_cue}" if case_by_id[value].target_cue else "")
                + (
                    f" · {case_by_id[value].created_at.strftime('%H:%M:%S')}"
                    if len(cases) > 1
                    else ""
                )
            ),
            key="case_id",
        )
    view = service.get_handoff_view(case_id)
    st.caption(
        f"SELECTED WALK · {resident.display_name} · {CONTEXTS[view.case.context_key]} · "
        f"{view.case.observed_on.isoformat()}"
    )

    left, right = st.columns([1.15, 1], gap="large")
    with left:
        result_area = st.empty()
        with result_area.container():
            retry = _result(view, mode)
            with st.expander("Note history"):
                for revision in service.history(case_id):
                    active = revision.id == view.case.active_revision_id
                    st.markdown(
                        f"**Version {revision.version} · {'Active' if active else 'Corrected'}**"
                    )
                    st.caption(revision.created_at.isoformat())
                    st.text(revision.body)
        if retry:
            result_area.empty()
            with result_area.container():
                st.info("Analyzing active note…")
            _analyze(service, case_id, mode)
            st.rerun()
    with right:
        _new_note(service, resident, view, mode)
        _baseline(service, view)
        _replacement(service, view, mode, result_area)

    st.divider()
    st.caption("This project is a prototype and is not medical advice.")


if __name__ == "__main__":
    main()
