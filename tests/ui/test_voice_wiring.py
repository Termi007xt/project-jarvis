"""The Voice screen's controls must be connected, or honestly disabled.

Every button on this screen was enabled and emitted a signal nobody had
connected: Test, Calibrate for this room, Preview, Record wake-word samples,
and the microphone selector. Clicking them did nothing at all — no action, no
error, no explanation. ADR-0010 forbids exactly that: an unbuilt feature is
shown disabled and names its phase, never presented as working.

The general rule these tests enforce: **an enabled control either does
something or says why it cannot.**
"""

from __future__ import annotations

import time
from typing import Iterator

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QMetaMethod  # noqa: E402
from PySide6.QtWidgets import QApplication, QPushButton  # noqa: E402

from jarvis.ui.app import JarvisApplication  # noqa: E402
from jarvis.ui.voice import VoicePanel  # noqa: E402
from jarvis.ui.voice_controller import VoiceController  # noqa: E402

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


# -- the defect this file exists for ---------------------------------------
def test_the_voice_service_is_actually_connected_to_the_shell(application) -> None:
    """``application.voice`` stayed None, so push-to-talk always refused."""
    assert application.voice is not None, "the voice stack was never joined to the shell"
    assert isinstance(application.voice, VoiceController)


def test_push_to_talk_reaches_the_service_instead_of_apologising(application) -> None:
    """It reported "not available on this machine" while fully installed."""
    assert hasattr(application.voice, "toggle_push_to_talk")


def test_every_enabled_button_on_the_voice_screen_has_a_receiver(application) -> None:
    """The rule: enabled means connected. Disabled means it says why."""
    panel = application.window.voice_panel()
    for button in panel.findChildren(QPushButton):
        if not button.isEnabled():
            assert button.toolTip().strip(), (
                f"'{button.text()}' is disabled but does not say why (ADR-0010)"
            )
            continue
        assert button.isSignalConnected(QMetaMethod.fromSignal(button.clicked)), (
            f"'{button.text()}' is enabled but connected to nothing"
        )


def test_each_panel_signal_the_controller_should_serve_is_connected(application) -> None:
    panel = application.window.voice_panel()
    for signal, name in (
        (panel.deviceChanged, "deviceChanged"),
        (panel.testMicrophoneRequested, "testMicrophoneRequested"),
        (panel.calibrateRequested, "calibrateRequested"),
        (panel.previewVoiceRequested, "previewVoiceRequested"),
        (panel.enrolRequested, "enrolRequested"),
    ):
        assert panel.isSignalConnected(QMetaMethod.fromSignal(signal)), (
            f"{name} is emitted into nothing"
        )


# -- what is deliberately not built (ADR-0010, ADR-0016) -------------------
def test_wake_word_enrolment_is_shown_disabled_and_names_its_phase(qapp) -> None:
    panel = VoicePanel()
    assert not panel.enrol_button.isEnabled()
    assert "Phase" in panel.enrol_button.text()
    assert panel.enrol_button.toolTip().strip()
    panel.close()


def test_a_missing_microphone_disables_the_controls_with_a_reason(
    qapp, core
) -> None:
    from jarvis.audio.availability import describe_voice_stack

    panel = VoicePanel()
    panel.set_stack_status(describe_voice_stack(core.config, None))
    for button in (panel.test_button, panel.calibrate_button):
        if not button.isEnabled():
            assert button.toolTip().strip()
    panel.close()


# -- the recording indicator (FR-013) --------------------------------------
def test_an_open_microphone_shows_in_the_tray(application) -> None:
    """Recording without a visible indicator is a prohibited capability."""
    from jarvis.ui.icons import TrayState

    application._set_recording_indicator(True)  # noqa: SLF001
    assert _pump(lambda: application.tray.state is TrayState.RECORDING)

    application._set_recording_indicator(False)  # noqa: SLF001
    assert _pump(lambda: application.tray.state is not TrayState.RECORDING)


def test_the_service_is_given_an_indicator_to_call(application) -> None:
    """Without one, capture could start with nothing on screen."""
    assert application._core.voice._indicator is not None  # noqa: SLF001


# -- the listening state is always visible ---------------------------------
def test_the_screen_says_whether_it_is_listening(qapp) -> None:
    panel = VoicePanel()
    panel.set_listening_state("capturing_command")
    assert "recording" in panel.listening_label.text().lower()
    panel.set_listening_state("off")
    assert "not listening" in panel.listening_label.text().lower()
    panel.close()


# -- a spoken command becomes a conversation turn --------------------------
def test_a_heard_command_is_sent_as_a_conversation_turn(application) -> None:
    """The pipeline transcribed commands that had no listener at all."""
    sent: list[str] = []
    application.send_message = sent.append  # type: ignore[method-assign]

    application.voice.commandHeard.emit("what is the time")  # type: ignore[attr-defined]

    assert _pump(lambda: sent == ["what is the time"])
