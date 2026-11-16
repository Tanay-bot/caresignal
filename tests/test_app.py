"""Exercise the actual screen and service through Streamlit's app runner."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from caresignal.fixtures import DEMO_NOTE, DEMO_REPLACEMENT
from caresignal.models import AssistanceLevel

APP = Path(__file__).resolve().parents[1] / "app.py"


def _app(monkeypatch, tmp_path):
    monkeypatch.setenv("CARESIGNAL_DATA_DIR", str(tmp_path))
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not app.exception
    return app


def _button(app, label):
    return next(button for button in app.button if button.label == label)


def _text(app):
    return "\n".join(
        str(element.value)
        for collection in (app.markdown, app.caption, app.subheader, app.text, app.info, app.error)
        for element in collection
    )


def test_same_note_different_resident_baselines(monkeypatch, tmp_path):
    app = _app(monkeypatch, tmp_path)
    assert "More help than usual" in _text(app)
    assert "Usual help:** Independent" in _text(app)
    assert DEMO_NOTE in _text(app)
    resident_selector = next(item for item in app.selectbox if item.label == "Fictional resident")
    resident_selector.select_index(1).run()
    assert not app.exception
    assert "Matches usual routine" in _text(app)
    assert "Usual help:** Staff beside or supervising" in _text(app)
    assert "More help than usual" not in _text(app)
    assert DEMO_NOTE in _text(app)
    assert "This project is a prototype and is not medical advice." in _text(app)


def test_replacement_clears_flag_and_preserves_original(monkeypatch, tmp_path):
    app = _app(monkeypatch, tmp_path)
    _button(app, "Use demo replacement").click().run()
    replacement = next(item for item in app.text_area if item.label == "Full replacement note")
    assert replacement.value == DEMO_REPLACEMENT
    _button(app, "Attach replacement").click().run()
    assert not app.exception
    rendered = _text(app)
    assert "More help than usual" not in rendered
    assert "Unclear" in rendered
    assert "Version 2 · Active" in rendered
    assert "Version 1 · Corrected" in rendered
    assert DEMO_REPLACEMENT in rendered
    assert DEMO_NOTE in rendered


def test_fixture_arbitrary_note_explains_live_mode(monkeypatch, tmp_path):
    app = _app(monkeypatch, tmp_path)
    note = next(item for item in app.text_area if item.label == "Complete shift note")
    note.input("She walked to breakfast independently on a new observation.")
    _button(app, "Analyze note").click().run()
    assert not app.exception
    rendered = _text(app)
    assert "More help than usual" not in rendered
    assert "Fixture" in rendered or "fixture" in rendered
    assert "Live" in rendered or "live" in rendered


def test_blank_replacement_preserves_source_and_input(monkeypatch, tmp_path):
    app = _app(monkeypatch, tmp_path)
    _button(app, "Attach replacement").click().run()
    assert not app.exception
    assert "Enter a nonblank replacement note" in _text(app)
    assert "More help than usual" in _text(app)
    assert "Version 2" not in _text(app)


def test_public_preset_exposes_frozen_original_and_uses_selected_mode(monkeypatch, tmp_path):
    app = _app(monkeypatch, tmp_path)
    app.radio[0].set_value("Phrase matcher").run()
    _button(app, "Load Fruta example").click().run()
    assert not app.exception
    rendered = _text(app)
    assert "nn_1093" in rendered
    assert "Mw. maakte een poging om zelf te lopen" in rendered
    assert "Fruta synthetic resident cn_04" in rendered
    assert "2024-03-07" in rendered
    assert "Analysis mode: phrase" in rendered
    assert "More help than usual" not in rendered


def test_baseline_requires_review_and_fresh_confirmation(monkeypatch, tmp_path):
    app = _app(monkeypatch, tmp_path)
    level = next(item for item in app.selectbox if item.label == "Specific usual help level")
    level.set_value(AssistanceLevel.SUPERVISION)
    description = next(
        item for item in app.text_area if item.label == "Staff-confirmed source description"
    )
    description.input("Usually has an aide beside her for the walk to breakfast.")
    _button(app, "Review usual assistance").click().run()
    assert not app.exception
    assert _button(app, "Confirm usual assistance").disabled
    app.checkbox[0].check().run()
    assert not _button(app, "Confirm usual assistance").disabled
    # Editing a reviewed record requires checking the new values again.
    description = next(
        item for item in app.text_area if item.label == "Staff-confirmed source description"
    )
    description.input("An aide walks alongside her to breakfast for support.")
    _button(app, "Review usual assistance").click().run()
    assert not app.exception
    assert _button(app, "Confirm usual assistance").disabled
    app.checkbox[0].check().run()
    _button(app, "Confirm usual assistance").click().run()
    assert not app.exception
    assert "Matches usual routine" in _text(app)
