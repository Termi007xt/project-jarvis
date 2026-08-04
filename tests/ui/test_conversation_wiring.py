"""The wiring between the Conversation screen and the engine.

The panel tests prove the screen emits what it should. They passed while the
screen was completely non-functional, because nothing tested the other half:
that ``send_message`` actually runs a turn and puts the answer on screen.

The defect they missed: the worker was a local variable with no parent QObject,
so PySide6 destroyed it the moment ``send_message`` returned. The thread
started, emitted ``started``, and the receiver no longer existed — no request,
no error, no log line, and a 2-second refresh timer quietly restored "Ready".

These tests drive the real signal path with a fake engine, so they are fast and
deterministic but exercise the same threading the GUI uses.
"""

from __future__ import annotations

import time
from typing import Iterator

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from jarvis.llm.conversation import Turn  # noqa: E402
from jarvis.llm.grounding import SourceLabel  # noqa: E402
from jarvis.ui.app import JarvisApplication  # noqa: E402

pytestmark = pytest.mark.ui


class FakeEngine:
    """Stands in for ConversationEngine. Blocks briefly, like the real one."""

    def __init__(self, *, available: bool = True, delay: float = 0.0) -> None:
        self.available = available
        self._delay = delay
        self.asked: list[str] = []

    def unavailable_reason(self) -> str | None:
        return None if self.available else "the fake engine is unavailable"

    def ask(self, conversation: object, text: str) -> Turn:
        self.asked.append(text)
        if self._delay:
            time.sleep(self._delay)
        return Turn(user_text=text, reply=f"answer to {text}", label=SourceLabel.MODEL_ANSWER)


class ExplodingEngine(FakeEngine):
    def ask(self, conversation: object, text: str) -> Turn:
        raise RuntimeError("the model runtime fell over")


@pytest.fixture
def application(qapp, core) -> Iterator[JarvisApplication]:
    app = JarvisApplication(core, qapp)
    yield app
    # Not JarvisApplication.quit(): that quits the QApplication, which is
    # session-scoped here, and shuts down the core the `core` fixture owns.
    app._refresh_timer.stop()  # noqa: SLF001
    # Leaving a conversation thread running takes the whole process down.
    app.stop_conversation_thread()
    app.bridge.detach()
    app.hotkeys.stop()
    if app.approvals is not None:
        app.approvals.panel.hide()
    app.tray.hide()
    app.window.close()


def _pump(condition, timeout: float = 10.0) -> bool:
    """Spin the Qt event loop until a condition holds, or give up."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False


# -- the defect this file exists for ---------------------------------------
def test_sending_a_message_actually_reaches_the_engine(application) -> None:
    """The worker must survive long enough to run. It did not."""
    engine = FakeEngine()
    application._core.conversation = engine  # noqa: SLF001

    application.send_message("what are you?")

    assert _pump(lambda: engine.asked), "the engine was never asked anything"
    assert engine.asked == ["what are you?"]


def test_the_reply_reaches_the_transcript(application) -> None:
    engine = FakeEngine()
    application._core.conversation = engine  # noqa: SLF001
    panel = application.window.conversation_panel()

    application.send_message("what are you?")

    assert _pump(lambda: "answer to what are you?" in panel.transcript_text()), (
        f"no reply appeared; transcript was {panel.transcript_text()!r}"
    )
    assert "from the local model" in panel.transcript_text()


def test_a_failing_turn_reports_the_failure_instead_of_going_quiet(application) -> None:
    """A silent failure is the worst outcome; it must always say something."""
    application._core.conversation = ExplodingEngine()  # noqa: SLF001
    panel = application.window.conversation_panel()

    application.send_message("break please")

    assert _pump(lambda: "could not answer" in panel.transcript_text().lower())
    assert "fell over" in panel.transcript_text()


def test_the_screen_becomes_usable_again_after_a_turn(application) -> None:
    engine = FakeEngine()
    application._core.conversation = engine  # noqa: SLF001
    panel = application.window.conversation_panel()

    application.send_message("hello")

    assert _pump(lambda: panel.input.isEnabled() and engine.asked)
    assert panel.send_button.isEnabled()


def test_the_thread_is_not_left_running_after_the_turn(application) -> None:
    """Each send created a QThread whose quit signal could never arrive."""
    engine = FakeEngine()
    application._core.conversation = engine  # noqa: SLF001

    application.send_message("hello")
    thread = application._conversation_thread  # noqa: SLF001
    assert thread is not None, "no worker thread was created"

    assert _pump(lambda: thread.isFinished()), (
        "the worker thread was still running after the turn finished"
    )
    # And the references are released, or every turn would leak one of each.
    assert _pump(lambda: application._conversation_worker is None)  # noqa: SLF001


def test_quitting_mid_turn_stops_the_thread_rather_than_abandoning_it(
    application,
) -> None:
    """Exiting with this thread running kills the process natively, not by
    exception — so shutdown has to wait for it."""
    engine = FakeEngine(delay=0.3)
    application._core.conversation = engine  # noqa: SLF001

    application.send_message("mid-flight")
    thread = application._conversation_thread  # noqa: SLF001
    assert thread is not None and thread.isRunning()

    assert application.stop_conversation_thread(timeout_ms=10_000)
    assert thread.isFinished()
    assert application._conversation_thread is None  # noqa: SLF001


# -- busy state (the refresh timer used to clobber it) ---------------------
def test_a_turn_in_flight_is_not_re_enabled_by_a_refresh(application) -> None:
    """refresh_conversation runs every 2 seconds and must not undo 'Thinking…'."""
    engine = FakeEngine(delay=0.5)
    application._core.conversation = engine  # noqa: SLF001
    panel = application.window.conversation_panel()

    application.send_message("slow one")
    assert not panel.input.isEnabled(), "the screen should be busy immediately"

    # Exactly what the 2-second timer does while the turn is still running.
    application.window.refresh_conversation()

    assert not panel.input.isEnabled(), "a refresh re-enabled input mid-turn"
    assert "thinking" in panel.status.text().lower()

    assert _pump(lambda: panel.input.isEnabled() and engine.asked, timeout=15.0)


def test_a_second_send_while_busy_does_not_start_a_second_turn(application) -> None:
    engine = FakeEngine(delay=0.4)
    application._core.conversation = engine  # noqa: SLF001

    application.send_message("first")
    application.send_message("second")

    assert _pump(lambda: engine.asked, timeout=15.0)
    time.sleep(0.2)
    QApplication.processEvents()
    assert engine.asked == ["first"], f"a second turn was started: {engine.asked}"


# -- unavailable engine ----------------------------------------------------
def test_an_unavailable_engine_says_so_and_asks_nothing(application) -> None:
    engine = FakeEngine(available=False)
    application._core.conversation = engine  # noqa: SLF001
    panel = application.window.conversation_panel()

    application.send_message("hello")

    assert engine.asked == []
    assert "unavailable" in panel.transcript_text().lower()
