"""Work handed to the GUI thread from a non-Qt thread must actually arrive.

`QTimer.singleShot(0, callback)` looks like a thread-safe way to run something
on the GUI thread. It is not. A timer cannot be created on a thread Qt did not
start, so when it is called from a plain `threading.Thread` the callback is
dropped — no exception, no log line, nothing.

Four things did exactly that, and all four were silently dead:

* **the emergency-stop hotkey** — the panic button, which SECURITY.md listed as
  reachable from the keyboard;
* **push-to-talk (F9)** — the hotkey registered correctly and then went nowhere,
  which is why it "did nothing";
* **the recording indicator** — FR-013, fired from the audio callback;
* **`notify.show`** — called on the invoker's worker thread, so the tool
  reported showing a notification that never appeared.

The rule these tests hold: anything crossing into the GUI thread does it with a
queued signal, and no `QTimer` is created off the GUI thread.
"""

from __future__ import annotations

import ast
import threading
import time
from typing import Iterator

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QObject, Qt, QTimer, Signal  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from jarvis.ui.app import JarvisApplication  # noqa: E402

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


def _from_a_plain_thread(work) -> None:
    """Exactly how a hotkey or audio callback reaches us."""
    thread = threading.Thread(target=work, name="not-a-qt-thread")
    thread.start()
    thread.join()


# -- the mechanism itself ---------------------------------------------------
def test_a_timer_started_off_the_gui_thread_never_fires(qapp) -> None:
    """The premise. If this ever starts passing, the workaround can go."""
    fired: list[str] = []
    _from_a_plain_thread(lambda: QTimer.singleShot(0, lambda: fired.append("x")))
    assert not _pump(lambda: fired, timeout=1.5), (
        "QTimer.singleShot now works across threads; revisit the marshalling"
    )


def test_a_queued_signal_from_a_plain_thread_does_arrive(qapp) -> None:
    class Marshal(QObject):
        ping = Signal(str)

    got: list[str] = []
    marshal = Marshal()
    marshal.ping.connect(got.append, Qt.ConnectionType.QueuedConnection)
    _from_a_plain_thread(lambda: marshal.ping.emit("hello"))
    assert _pump(lambda: got == ["hello"])


# -- the emergency stop, which is the one that matters --------------------
def test_the_emergency_stop_hotkey_reaches_the_core(application) -> None:
    """PRD 11.3: this is the panic button. It did nothing at all."""
    stopped: list[str] = []
    application._core.emergency_stop = lambda origin="hotkey": (  # noqa: SLF001
        stopped.append(origin) or _FakeReport()
    )

    binding = application.hotkeys.binding("emergency_stop")
    assert binding is not None, "emergency stop was never bound"
    _from_a_plain_thread(binding.action)

    assert _pump(lambda: stopped), "the emergency stop hotkey did not reach the core"
    assert stopped == ["hotkey"]


class _FakeReport:
    def describe(self) -> str:
        return "stopped"


# -- push to talk -----------------------------------------------------------
def test_the_push_to_talk_hotkey_reaches_the_voice_service(application) -> None:
    pressed: list[bool] = []
    application.push_to_talk = lambda: pressed.append(True)  # type: ignore[method-assign]

    binding = application.hotkeys.binding("push_to_talk")
    assert binding is not None, "push-to-talk was never bound"
    _from_a_plain_thread(binding.action)

    assert _pump(lambda: pressed), "F9 registered but the action never ran"


# -- the recording indicator (FR-013) --------------------------------------
def test_the_recording_indicator_updates_from_the_audio_thread(application) -> None:
    from jarvis.ui.icons import TrayState

    _from_a_plain_thread(lambda: application._set_recording_indicator(True))  # noqa: SLF001
    assert _pump(lambda: application.tray.state is TrayState.RECORDING), (
        "an open microphone did not reach the tray"
    )

    _from_a_plain_thread(lambda: application._set_recording_indicator(False))  # noqa: SLF001
    assert _pump(lambda: application.tray.state is not TrayState.RECORDING)


# -- notify.show ------------------------------------------------------------
def test_a_tool_notification_from_a_worker_thread_arrives(application) -> None:
    """The tool reported success for a notification that never appeared."""
    shown: list[tuple[str, str]] = []
    application.tray.notify = lambda title, message, seconds=5: shown.append(  # type: ignore[method-assign]
        (title, message)
    )
    application.notificationRequested.disconnect()
    application.notificationRequested.connect(
        application.tray.notify, Qt.ConnectionType.QueuedConnection
    )

    _from_a_plain_thread(lambda: application._notify_from_tool("Title", "Body"))  # noqa: SLF001

    assert _pump(lambda: shown == [("Title", "Body")])


# -- the rule, enforced statically -----------------------------------------
def test_no_qtimer_is_created_outside_the_gui_thread() -> None:
    """Any new QTimer.singleShot in the shell must be on the GUI thread.

    Checked by hand rather than by rule: the AST cannot know which thread a
    call runs on, so this pins the count and forces a deliberate decision.
    """
    from jarvis.ui import app as app_module

    source = ast.parse(open(app_module.__file__, encoding="utf-8").read())
    single_shots = [
        node
        for node in ast.walk(source)
        if isinstance(node, ast.Call)
        and getattr(node.func, "attr", None) == "singleShot"
    ]
    assert not single_shots, (
        "jarvis.ui.app uses QTimer.singleShot again. It silently does nothing "
        "when called from a hotkey, audio or worker thread — use a queued "
        "signal instead, or add the call here with a note saying why the GUI "
        "thread is guaranteed."
    )
