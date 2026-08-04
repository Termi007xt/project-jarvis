"""How Jarvis behaves when it was spoken to, and who it thinks you are.

From a real session:

* Asking "what time is it right now?" produced a **completely blank reply**,
  twice, under a confident source label. The model returned no text and the
  screen rendered nothing, which is indistinguishable from being ignored.
* Speaking **yanked the Conversation window to the front every time**, even
  with the app minimised to the tray. Speaking is meant to be the way to use
  Jarvis *without* the window.
* A spoken question was answered **in writing only**, so the answer was
  invisible unless you went and looked — which is the same problem again.
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
    available = True

    def __init__(self, reply: str = "the time is four o'clock") -> None:
        self.reply = reply
        self.asked: list[str] = []

    def unavailable_reason(self) -> str | None:
        return None

    def ask(self, conversation: object, text: str) -> Turn:
        self.asked.append(text)
        return Turn(user_text=text, reply=self.reply, label=SourceLabel.MODEL_ANSWER)


@pytest.fixture
def application(qapp, core) -> Iterator[JarvisApplication]:
    # No test opens the speakers. Cue playback is real audio output, and a
    # stream left open at interpreter exit corrupts the heap on the way out.
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


def _pump(condition, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False


# -- speaking does not take over the screen --------------------------------
def test_a_spoken_command_does_not_raise_the_window(application) -> None:
    """It did this every time, including from the tray with nothing open."""
    application._core.conversation = FakeEngine()  # noqa: SLF001
    application.window.hide()
    QApplication.processEvents()

    application._on_command_heard("what is the time")  # noqa: SLF001
    QApplication.processEvents()

    assert not application.window.isVisible(), (
        "speaking pulled the window to the front; that is what the tray is for"
    )


def test_a_spoken_command_still_reaches_the_engine(application) -> None:
    engine = FakeEngine()
    application._core.conversation = engine  # noqa: SLF001
    application._on_command_heard("what is the time")  # noqa: SLF001
    assert _pump(lambda: engine.asked == ["what is the time"])


# -- and the answer is spoken back -----------------------------------------
def test_a_spoken_question_is_answered_aloud(application) -> None:
    engine = FakeEngine("the time is four o'clock")
    application._core.conversation = engine  # noqa: SLF001
    spoken: list[str] = []
    application.voice.speak_reply = spoken.append  # type: ignore[attr-defined]

    application._on_command_heard("what is the time")  # noqa: SLF001

    assert _pump(lambda: spoken == ["the time is four o'clock"])


def test_a_typed_question_is_not_answered_aloud(application) -> None:
    """Typing means you are looking at the screen. Do not talk over it."""
    engine = FakeEngine()
    application._core.conversation = engine  # noqa: SLF001
    spoken: list[str] = []
    application.voice.speak_reply = spoken.append  # type: ignore[attr-defined]

    application.send_message("what is the time")

    assert _pump(lambda: engine.asked)
    time.sleep(0.2)
    QApplication.processEvents()
    assert spoken == []


def test_a_failure_after_a_spoken_command_is_also_announced(application) -> None:
    """Otherwise a voice failure is completely silent and invisible."""

    class Broken(FakeEngine):
        def ask(self, conversation: object, text: str) -> Turn:
            raise RuntimeError("the model fell over")

    application._core.conversation = Broken()  # noqa: SLF001
    spoken: list[str] = []
    application.voice.speak_reply = spoken.append  # type: ignore[attr-defined]

    application._on_command_heard("what is the time")  # noqa: SLF001

    assert _pump(lambda: spoken)
    assert "did not work" in spoken[0].lower()


def test_the_aloud_flag_does_not_leak_into_the_next_typed_turn(application) -> None:
    engine = FakeEngine()
    application._core.conversation = engine  # noqa: SLF001
    spoken: list[str] = []
    application.voice.speak_reply = spoken.append  # type: ignore[attr-defined]

    application._on_command_heard("first")  # noqa: SLF001
    assert _pump(lambda: len(spoken) == 1)
    # A second turn cannot start until the first one's thread has stopped.
    assert _pump(lambda: application._conversation_worker is None)  # noqa: SLF001

    application.send_message("second typed")
    assert _pump(lambda: engine.asked == ["first", "second typed"])
    time.sleep(0.2)
    QApplication.processEvents()
    assert len(spoken) == 1, "a typed turn was spoken because the flag persisted"


# -- audio cues -------------------------------------------------------------
def test_a_spoken_command_plays_a_thinking_cue(application) -> None:
    played: list[str] = []
    application.voice.play_cue = played.append  # type: ignore[attr-defined]
    application._core.conversation = FakeEngine()  # noqa: SLF001

    application._on_command_heard("what is the time")  # noqa: SLF001

    from jarvis.audio.cues import Cue

    assert played == [Cue.THINKING]


def test_the_wake_cue_plays_when_recording_starts(application) -> None:
    from jarvis.audio.cues import Cue

    played: list[str] = []
    application.voice.play_cue = played.append  # type: ignore[attr-defined]

    application.voice._on_state("capturing_command")  # noqa: SLF001

    assert played == [Cue.WAKE]


def test_no_cue_for_states_that_are_not_events(application) -> None:
    played: list[str] = []
    application.voice.play_cue = played.append  # type: ignore[attr-defined]
    application.voice._on_state("off")  # noqa: SLF001
    application.voice._on_state("waiting_for_wake")  # noqa: SLF001
    assert played == []


# -- the user's name --------------------------------------------------------
def test_the_transcript_uses_the_name_instead_of_you(application) -> None:
    panel = application.window.conversation_panel()
    panel.set_user_name("Maulik")
    panel.append_user("hello")
    assert "Maulik:" in panel.transcript_text()
    assert "You:" not in panel.transcript_text()


def test_an_empty_name_falls_back_to_you(qapp, core) -> None:
    from jarvis.ui.conversation import ConversationPanel

    panel = ConversationPanel(core)
    panel.set_user_name("")
    panel.append_user("hello")
    assert "You:" in panel.transcript_text()
    panel.close()


def test_the_name_persists(application) -> None:
    application.set_user_name("Maulik Sharma")
    assert application._core.config.ui.user_name == "Maulik Sharma"  # noqa: SLF001


def test_the_model_is_told_the_name(application) -> None:
    application.set_user_name("Maulik")
    engine = application._core.conversation  # noqa: SLF001
    conversation = application._core.start_conversation(private=True)  # noqa: SLF001

    messages = engine._build_context(conversation)  # noqa: SLF001
    assert "Maulik" in messages[0].content, "the model was never told the name"


def test_setting_the_name_programmatically_does_not_re_emit(qapp, core) -> None:
    from jarvis.ui.conversation import ConversationPanel

    panel = ConversationPanel(core)
    emitted: list[str] = []
    panel.userNameChanged.connect(emitted.append)
    panel.set_user_name("Maulik")
    assert emitted == []
    panel.close()
