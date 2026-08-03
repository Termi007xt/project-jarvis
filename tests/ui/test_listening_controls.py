"""Turning listening on and off, and saying what was heard.

Two changes the owner asked for after using the build:

* **Always-listening without a personal enrolment.** ADR-0016 originally gated
  it on a measured enrolment; that flow is not built, so the toggle could never
  be enabled and the screen said "Jarvis is not listening" with no way to
  change it. The gate is now whether the wake detector actually loads
  (amendment recorded in ADR-0016).
* **Push-to-talk is optional**, because it was the only route and it was dead.

Plus one thing that was missing entirely: the screen never showed what it
transcribed, so a misheard word looked like a bad answer rather than a bad
transcription.
"""

from __future__ import annotations

import time
from typing import Iterator

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from jarvis.ui.app import JarvisApplication  # noqa: E402
from jarvis.ui.voice import VoicePanel  # noqa: E402

pytestmark = pytest.mark.ui


@pytest.fixture
def application(qapp, core) -> Iterator[JarvisApplication]:
    app = JarvisApplication(core, qapp)
    yield app
    app._refresh_timer.stop()  # noqa: SLF001
    app.stop_conversation_thread()
    if app.voice is not None:
        app.voice.shutdown()  # type: ignore[attr-defined]
    app.bridge.detach()
    app.hotkeys.stop()
    if app.approvals is not None:
        app.approvals.panel.hide()
    app.tray.hide()
    app.window.close()


def _pump(condition, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False


# -- the transcript, which was never shown ---------------------------------
def test_the_screen_shows_what_was_transcribed(qapp) -> None:
    panel = VoicePanel()
    panel.set_last_heard("what is the time", 0.75)
    assert "what is the time" in panel.heard_label.text()
    assert "75" in panel.heard_label.text()
    panel.close()


def test_hearing_nothing_says_so_rather_than_staying_blank(qapp) -> None:
    panel = VoicePanel()
    panel.set_last_heard("", None)
    assert "nothing was heard" in panel.heard_label.text().lower()
    panel.close()


def test_a_transcript_with_no_confidence_still_shows(qapp) -> None:
    panel = VoicePanel()
    panel.set_last_heard("open brave", None)
    assert "open brave" in panel.heard_label.text()
    panel.close()


def test_a_heard_command_reaches_the_screen(application) -> None:
    panel = application.window.voice_panel()
    application.voice.heard.emit("play some music", 0.9)  # type: ignore[attr-defined]
    assert _pump(lambda: "play some music" in panel.heard_label.text())


# -- the listening toggle ---------------------------------------------------
def test_listening_is_offered_when_the_detector_loads_not_when_enrolled(qapp) -> None:
    """The old gate was an enrolment flow that does not exist in this build."""
    panel = VoicePanel()
    panel.set_listening_available(True)
    assert panel.listen_button.isEnabled()
    panel.close()


def test_listening_is_refused_with_a_reason_when_the_model_is_missing(qapp) -> None:
    panel = VoicePanel()
    panel.set_listening_available(False, "No wake-word model is installed.")
    assert not panel.listen_button.isEnabled()
    assert "wake-word model" in panel.listen_button.toolTip()
    panel.close()


def test_the_toggle_says_which_way_it_goes(qapp) -> None:
    panel = VoicePanel()
    panel.set_listening(False)
    assert panel.listen_button.text() == "Start listening"
    panel.set_listening(True)
    assert panel.listen_button.text() == "Stop listening"
    panel.close()


def test_setting_the_toggle_programmatically_does_not_re_emit(qapp) -> None:
    """Otherwise a refresh every 2 seconds would restart the microphone."""
    panel = VoicePanel()
    emitted: list[bool] = []
    panel.alwaysListeningToggled.connect(emitted.append)
    panel.set_listening(True)
    panel.set_listening(False)
    assert emitted == []
    panel.close()


def test_the_wake_phrase_line_no_longer_claims_jarvis_is_not_listening(qapp) -> None:
    """It said that permanently, with no way for the user to change it."""
    panel = VoicePanel()
    panel.set_phrase("Hey Jarvis", enrolled=False)
    assert "not listening" not in panel.phrase_label.text().lower()
    assert "Hey Jarvis" in panel.phrase_label.text()
    panel.close()


def test_the_screen_still_refuses_to_imply_bare_jarvis_works(qapp) -> None:
    """FR-011 survives the rewording."""
    panel = VoicePanel()
    panel.set_phrase("Hey Jarvis", enrolled=False)
    panel.set_enrolment("Using the pretrained model.", passed=False, enrolled=False)
    assert not panel.claims_single_word_phrase()
    panel.close()


# -- push-to-talk is optional ----------------------------------------------
def test_push_to_talk_shows_its_key(qapp) -> None:
    panel = VoicePanel()
    panel.set_push_to_talk(True, "F9")
    assert "F9" in panel.push_to_talk_toggle.text()
    assert panel.push_to_talk_toggle.isChecked()
    panel.close()


def test_turning_push_to_talk_off_stops_the_hotkey_opening_the_microphone(
    application,
) -> None:
    """Off must mean off — not "opens the mic and says it is off"."""
    panel = application.window.voice_panel()
    panel.set_push_to_talk(False, "F9")

    opened: list[bool] = []
    application._core.voice.begin_push_to_talk = lambda: (  # noqa: SLF001
        opened.append(True) or True
    )

    application.voice.toggle_push_to_talk()  # type: ignore[attr-defined]
    QApplication.processEvents()
    assert opened == [], "push-to-talk was off but still opened the microphone"


def test_setting_push_to_talk_programmatically_does_not_re_emit(qapp) -> None:
    panel = VoicePanel()
    emitted: list[bool] = []
    panel.pushToTalkToggled.connect(emitted.append)
    panel.set_push_to_talk(True, "F9")
    panel.set_push_to_talk(False, "F9")
    assert emitted == []
    panel.close()


# -- the settings survive a restart ----------------------------------------
def test_toggling_listening_persists_the_choice(application) -> None:
    saved: list[tuple[str, object]] = []
    application._persist_setting = lambda key, value: saved.append((key, value))  # noqa: SLF001
    application.voice.settingChanged.disconnect()  # type: ignore[attr-defined]
    application.voice.settingChanged.connect(application._persist_setting)  # type: ignore[attr-defined]

    application.voice.set_listening(False)  # type: ignore[attr-defined]
    QApplication.processEvents()

    assert ("audio.wake_word.always_listening", False) in saved


def test_toggling_push_to_talk_persists_the_choice(application) -> None:
    application.voice.set_push_to_talk_enabled(False)  # type: ignore[attr-defined]
    QApplication.processEvents()
    assert application._core.config.audio.wake_word.push_to_talk_enabled is False  # noqa: SLF001
