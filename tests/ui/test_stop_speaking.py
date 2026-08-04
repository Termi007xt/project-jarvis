"""Making Jarvis shut up — the route that does not depend on tuning.

Reported from real use: "i am not able to interrupt it for some reason."

Acoustic barge-in has thresholds, and thresholds need measuring on real
hardware in a real room. A panic button does not: pressing a key is
unambiguous. Two defects made the keyboard route useless anyway.

* **Emergency stop never stopped speech.** `JarvisCore.emergency_stop` cancels
  tasks, releases locks, stops workers and denies approvals. Speech is none of
  those, so `Ctrl+Alt+End` left Jarvis talking over the silence it had just
  created — the one thing the user could actually hear.
* **There was no "stop talking" that was not also "stop everything".** ADR-0028
  is explicit that barge-in must not release locks or cancel tasks, so the tray
  needs its own entry rather than borrowing the emergency stop.
"""

from __future__ import annotations

from typing import Iterator

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from jarvis.ui.app import JarvisApplication  # noqa: E402

pytestmark = pytest.mark.ui


@pytest.fixture
def application(qapp, core) -> Iterator[JarvisApplication]:
    core.set_setting("audio.cues_enabled", False)
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


def _speaking(application: JarvisApplication):
    """Put the pipeline into the state it is in while Kokoro plays."""
    if application.voice is None:
        pytest.skip("no voice stack on this machine")
    service = application.voice._voice  # noqa: SLF001
    service.pipeline.speaking_started("a long answer nobody wants to sit through")
    return service.pipeline.duplex


# -- the panic button ------------------------------------------------------
def test_emergency_stop_also_stops_speech(application) -> None:
    duplex = _speaking(application)
    application.emergency_stop()
    QApplication.processEvents()
    assert duplex.stop_requested, "Ctrl+Alt+End left Jarvis talking"


def test_emergency_stop_from_the_hotkey_also_stops_speech(application) -> None:
    duplex = _speaking(application)
    application.emergency_stop_from_hotkey()
    QApplication.processEvents()
    assert duplex.stop_requested


def test_emergency_stop_still_stops_the_automation(application) -> None:
    """Silencing speech must not have replaced what it already did."""
    stopped: list[str] = []
    application._core.emergency_stop = lambda origin="api": stopped.append(origin) or _Report()  # noqa: SLF001
    application.emergency_stop()
    assert stopped == ["tray"]


class _Report:
    def describe(self) -> str:
        return "nothing to stop"


# -- stop talking, and only that -------------------------------------------
def test_the_tray_offers_stop_speaking(application) -> None:
    action = application.tray.action_stop_speaking
    assert action.isEnabled()
    assert "speak" in action.text().lower()


def test_the_tray_entry_stops_speech(application) -> None:
    duplex = _speaking(application)
    application.tray.action_stop_speaking.trigger()
    QApplication.processEvents()
    assert duplex.stop_requested


def test_stopping_speech_cancels_nothing_and_releases_nothing(application) -> None:
    """ADR-0028: barge-in is not emergency stop, and conflating them is
    exactly how "stop talking" becomes quietly destructive."""
    stopped: list[str] = []
    application._core.emergency_stop = lambda origin="api": stopped.append(origin)  # noqa: SLF001
    _speaking(application)
    application.stop_speaking()
    assert stopped == []


def test_stopping_speech_when_silent_is_harmless(application) -> None:
    if application.voice is None:
        pytest.skip("no voice stack on this machine")
    application.stop_speaking()  # nothing is playing
    QApplication.processEvents()


def test_stop_speaking_survives_a_missing_voice_stack(application) -> None:
    """The tray entry exists whether or not Kokoro is installed."""
    application.voice = None
    application.stop_speaking()
    application.emergency_stop()
