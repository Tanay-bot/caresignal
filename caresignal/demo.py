"""Replay the offline walkthrough through the same service used by the app."""

import json
import tempfile
from pathlib import Path

from .extractors import FixtureExtractor
from .fixtures import DEMO_REPLACEMENT
from .service import CareSignalService


def run_demo(db_path: str | Path, workspace_id: str = "cli-walkthrough") -> dict:
    service = CareSignalService(db_path, workspace_id)
    cases = service.reset_demo()
    before = []
    for case in cases:
        view = service.get_handoff_view(case.id)
        before.append(
            {
                "resident": view.resident.display_name,
                "documented_help": view.run.result.label.value,
                "usual_help": view.baseline.level.value,
                "comparison": view.comparison.status,
                "note": view.revision.body,
                "evidence": [span.quote for span in view.run.result.evidence],
            }
        )
    elena = next(
        case for case in cases if service.get_handoff_view(case.id).resident.display_name == "Elena"
    )
    service.replace_active_revision(elena.id, elena.active_revision_id, DEMO_REPLACEMENT)
    service.analyze_active_revision(elena.id, FixtureExtractor())
    after = service.get_handoff_view(elena.id)
    return {
        "mode": "fixture",
        "before": before,
        "after_replacement": {
            "resident": after.resident.display_name,
            "documented_help": after.run.result.label.value,
            "comparison": after.comparison.status,
            "active_version": after.revision.version,
            "history_versions": [revision.version for revision in service.history(elena.id)],
            "note": after.revision.body,
        },
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="caresignal-walkthrough-") as directory:
        print(json.dumps(run_demo(Path(directory) / "demo.sqlite3"), indent=2))


if __name__ == "__main__":
    main()
