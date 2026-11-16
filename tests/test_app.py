"""Exercise the actual screen and service through Streamlit's app runner."""

from html.parser import HTMLParser
from pathlib import Path

from streamlit.testing.v1 import AppTest

from caresignal import extractors
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
        for collection in (
            app.markdown,
            app.html,
            app.caption,
            app.subheader,
            app.text,
            app.info,
            app.error,
        )
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
    # An invalid edit must also invalidate the previously reviewed confirmation.
    description = next(
        item for item in app.text_area if item.label == "Staff-confirmed source description"
    )
    description.input(" ")
    _button(app, "Review usual assistance").click().run()
    assert not app.exception
    assert "Add a source description" in _text(app)
    assert not any(item.label == "Confirm usual assistance" for item in app.button)
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


def test_gemini_provider_routes_all_note_actions_without_openai(monkeypatch, tmp_path):
    calls = []

    class MockGeminiExtractor:
        mode = "gemini"
        version = "mock-gemini-v1"
        model_id = "gemini-test-model"
        prompt_version = "walking-assistance-v1"

        def extract(self, note_body, target, revision_id):
            calls.append((note_body, target, revision_id))
            return extractors.FixtureExtractor().extract(note_body, target, revision_id)

    class UnexpectedOpenAIExtractor:
        def __init__(self):
            raise AssertionError("Gemini selection must never construct the OpenAI adapter")

    monkeypatch.setenv("GEMINI_API_KEY", "test-only-not-a-real-key")
    monkeypatch.setattr(extractors, "GeminiExtractor", MockGeminiExtractor)
    monkeypatch.setattr(extractors, "OpenAIExtractor", UnexpectedOpenAIExtractor)
    app = _app(monkeypatch, tmp_path)
    app.radio[0].set_value("Live AI").run()
    assert not app.exception
    provider = next(item for item in app.selectbox if item.label == "AI provider")
    assert provider.value == "Gemini"
    assert "Configured model: gemini-test-model" in _text(app)

    _button(app, "Analyze active note").click().run()
    assert not app.exception
    assert "Analysis mode: gemini" in _text(app)
    assert "model gemini-test-model" in _text(app)
    _button(app, "Use demo replacement").click().run()
    _button(app, "Attach replacement").click().run()
    assert not app.exception
    assert "Version 2 · Active" in _text(app)
    assert "More help than usual" not in _text(app)
    _button(app, "Analyze note").click().run()
    assert not app.exception
    _button(app, "Load Fruta example").click().run()
    assert not app.exception
    assert "Hands-on help" in _text(app)
    _button(app, "Analyze active note").click().run()
    assert not app.exception
    assert len(calls) == 5
    assert [call[0] for call in calls[:3]] == [DEMO_NOTE, DEMO_REPLACEMENT, DEMO_NOTE]
    assert calls[3][2] == calls[4][2]  # A retry stays scoped to the same active revision.


def test_gemini_missing_key_is_retryable_and_clears_prior_flag(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_MODEL", "gemini-configured-test-model")
    app = _app(monkeypatch, tmp_path)
    app.radio[0].set_value("Live AI").run()
    provider = next(item for item in app.selectbox if item.label == "AI provider")
    assert provider.value == "OpenAI"
    provider.set_value("Gemini").run()
    assert not app.exception
    assert "Set GEMINI_API_KEY to enable Gemini extraction" in _text(app)
    assert "Configured model: gemini-configured-test-model" in _text(app)
    _button(app, "Analyze active note").click().run()
    assert not app.exception
    rendered = _text(app)
    assert "Analysis unavailable" in rendered
    assert "missing_credentials" in rendered
    assert "More help than usual" not in rendered
    assert "Analysis mode: gemini" in rendered
    assert _button(app, "Retry active note")
    # Checking an offline mode should not discard an explicitly selected provider.
    app.radio[0].set_value("Fixture demo").run()
    app.radio[0].set_value("Live AI").run()
    provider = next(item for item in app.selectbox if item.label == "AI provider")
    assert provider.value == "Gemini"


def test_changing_method_identifies_the_existing_result_until_reanalysis(monkeypatch, tmp_path):
    app = _app(monkeypatch, tmp_path)
    app.radio[0].set_value("Phrase matcher").run()
    assert not app.exception
    rendered = _text(app)
    assert "Selected method: Phrase matcher" in rendered
    assert "Analysis mode: fixture (Fixture demo)" in rendered
    assert "This result used Fixture demo" in rendered
    _button(app, "Analyze active note").click().run()
    assert not app.exception
    rendered = _text(app)
    assert "Analysis mode: phrase (Phrase matcher)" in rendered
    assert "This result used Fixture demo" not in rendered


def test_replacing_public_note_removes_old_highlights_and_source_original(monkeypatch, tmp_path):
    app = _app(monkeypatch, tmp_path)
    _button(app, "Load Fruta example").click().run()
    assert not app.exception
    assert "Hands-on help" in _text(app)
    assert any(item.label == "Original Dutch text" for item in app.expander)
    assert not any(item.label == "Use demo replacement" for item in app.button)
    replacement = next(item for item in app.text_area if item.label == "Full replacement note")
    replacement.input("The resident ate breakfast. No walking event was documented.")
    _button(app, "Attach replacement").click().run()
    assert not app.exception
    assert "Hands-on help" not in _text(app)
    assert "Version 2 · Active" in _text(app)
    assert "Version 1 · Corrected" in _text(app)
    assert not any(item.label == "Original Dutch text" for item in app.expander)
    current_source = next(
        item.value for item in app.html if '<div class="source-note">' in item.value
    )
    assert "No walking event was documented." in current_source
    assert "<mark>" not in current_source


def test_source_markdown_and_html_are_preserved_as_literal_text(monkeypatch, tmp_path):
    class SourceParser(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.tags = []
            self.fragments = []

        def handle_starttag(self, tag, attrs):
            self.tags.append(tag)

        def handle_data(self, data):
            self.fragments.append(data)

    note = (
        "She walked to breakfast.\n\n# SOURCE HEADING\n\n"
        "[Source label](https://example.org)\n\n<b>Literal text</b> & evidence"
    )
    app = _app(monkeypatch, tmp_path)
    next(item for item in app.text_area if item.label == "Complete shift note").input(note)
    _button(app, "Analyze note").click().run()
    assert not app.exception
    source_html = next(item.value for item in app.html if '<div class="source-note">' in item.value)
    source = SourceParser()
    source.feed(source_html)
    assert "".join(source.fragments) == note
    assert source.tags == ["div"]  # Neither Markdown nor source HTML becomes an element.
    assert not any(note in item.value for item in app.markdown)

    baseline = "Usually walks independently.\n\n# BASELINE HEADING\n\n[Source](https://example.org)"
    next(
        item for item in app.text_area if item.label == "Staff-confirmed source description"
    ).input(baseline)
    _button(app, "Review usual assistance").click().run()
    assert not app.exception
    assert f"Source description: {baseline}" in [item.value for item in app.text]
    app.checkbox[0].check().run()
    _button(app, "Confirm usual assistance").click().run()
    assert not app.exception
    assert baseline in [item.value for item in app.text]
    assert not any(baseline in item.value for item in app.markdown)
