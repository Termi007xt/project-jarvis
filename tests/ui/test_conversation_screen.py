"""The Conversation screen (PRD section 9.5, FR-046, FR-047)."""

from __future__ import annotations

from typing import Iterator

import pytest

pytest.importorskip("PySide6")

from jarvis.llm.grounding import SourceLabel  # noqa: E402
from jarvis.ui.conversation import ConversationPanel  # noqa: E402
from jarvis.ui.main_window import MainWindow  # noqa: E402

pytestmark = pytest.mark.ui


@pytest.fixture
def panel(qapp, core) -> Iterator[ConversationPanel]:
    widget = ConversationPanel(core)
    yield widget
    widget.close()
    widget.deleteLater()


# -- source labelling (FR-047) ---------------------------------------------
def test_every_reply_is_labelled_with_where_it_came_from(panel: ConversationPanel) -> None:
    panel.append_reply("Paris.", SourceLabel.MODEL_ANSWER)
    panel.append_reply("Brave is open.", SourceLabel.TOOL_RESULT)
    panel.append_reply("Probably.", SourceLabel.UNCERTAINTY)

    text = panel.transcript_text()
    assert "from the local model" in text
    assert "confirmed by a tool" in text
    assert "uncertain" in text


def test_a_tool_confirmed_answer_reads_differently_from_a_model_answer(
    panel: ConversationPanel,
) -> None:
    """The distinction is the whole point of FR-047."""
    panel.append_reply("Brave is open.", SourceLabel.MODEL_ANSWER)
    first = panel.transcript_text()
    panel.clear_transcript()
    panel.append_reply("Brave is open.", SourceLabel.TOOL_RESULT)
    assert panel.transcript_text() != first


def test_every_source_label_has_display_wording(panel: ConversationPanel) -> None:
    for label in SourceLabel:
        panel.clear_transcript()
        panel.append_reply("x", label)
        assert panel.transcript_text().strip() != "x"


# -- untrusted rendering ----------------------------------------------------
def test_model_output_is_escaped_rather_than_rendered(panel: ConversationPanel) -> None:
    """Model output is data here too, including in the transcript."""
    panel.append_reply("<script>alert(1)</script>", SourceLabel.MODEL_ANSWER)
    html = panel.transcript.toHtml()
    assert "<script>alert(1)</script>" not in html
    assert "alert(1)" in panel.transcript_text()


def test_user_text_is_escaped_too(panel: ConversationPanel) -> None:
    panel.append_user("<b>not bold</b>")
    assert "not bold" in panel.transcript_text()
    assert "<b>not bold</b>" not in panel.transcript.toHtml()


# -- availability (ADR-0010) -----------------------------------------------
def test_an_unavailable_model_disables_input_and_says_why(panel: ConversationPanel) -> None:
    panel.set_availability(False, "Offline mode is enabled, so Jarvis makes no request.")
    assert not panel.input.isEnabled()
    assert not panel.send_button.isEnabled()
    assert "Offline mode" in panel.status.text()


def test_an_available_model_enables_input(panel: ConversationPanel) -> None:
    panel.set_availability(True, None)
    assert panel.input.isEnabled()
    assert panel.send_button.isEnabled()


def test_a_missing_reason_still_produces_an_explanation(panel: ConversationPanel) -> None:
    panel.set_availability(False, None)
    assert panel.status.text().strip()


# -- private session (FR-046) ----------------------------------------------
def test_a_private_session_is_visible_in_the_transcript(panel: ConversationPanel) -> None:
    panel.set_private(True)
    assert "nothing from here is written" in panel.transcript_text().lower()


def test_the_private_toggle_does_not_re_emit_when_set_programmatically(
    panel: ConversationPanel,
) -> None:
    emitted: list[bool] = []
    panel.privateSessionToggled.connect(emitted.append)
    panel.set_private(True)
    assert emitted == []


def test_toggling_private_by_hand_emits(panel: ConversationPanel) -> None:
    emitted: list[bool] = []
    panel.privateSessionToggled.connect(emitted.append)
    panel.private_toggle.setChecked(True)
    assert emitted == [True]


# -- sending ---------------------------------------------------------------
def test_sending_emits_the_text_and_clears_the_box(panel: ConversationPanel) -> None:
    sent: list[str] = []
    panel.sendRequested.connect(sent.append)
    panel.input.setText("  open Brave  ")
    panel._send()  # noqa: SLF001
    assert sent == ["open Brave"]
    assert panel.input.text() == ""


def test_sending_nothing_does_nothing(panel: ConversationPanel) -> None:
    sent: list[str] = []
    panel.sendRequested.connect(sent.append)
    panel.input.setText("   ")
    panel._send()  # noqa: SLF001
    assert sent == []


def test_being_busy_prevents_a_second_send(panel: ConversationPanel) -> None:
    panel.set_busy(True)
    assert not panel.input.isEnabled()
    assert not panel.send_button.isEnabled()
    panel.set_busy(False)
    assert panel.input.isEnabled()


# -- the screen is live in the window --------------------------------------
def test_conversation_is_a_live_area_not_a_phase_placeholder(qapp, core) -> None:
    window = MainWindow(core)
    assert "conversation" in window.live_area_keys()
    window.refresh_conversation()
    assert window.conversation_panel().status.text().strip()
    window.close()


def test_the_home_screen_reports_the_voice_stack_honestly(qapp, core) -> None:
    window = MainWindow(core)
    window.refresh_home()
    text = window._text("home").body.toPlainText()  # noqa: SLF001
    assert "Voice stack" in text
    # Nothing may claim to be available when it is not installed.
    assert "Speech recognition" in text
    window.close()
