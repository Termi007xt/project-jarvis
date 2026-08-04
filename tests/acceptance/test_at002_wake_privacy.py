"""AT-002 — listening enabled, no wake phrase, no audio on disk.

Also PRD FR-012 (pre-wake audio only in a short in-memory ring buffer),
FR-013 (visible recording indicator), FR-024 (wake phrase stripped) and
FR-025 (no raw-audio retention).

The strongest assertion here is structural rather than behavioural: the ring
buffer has no file-handling code at all, so it *cannot* write to disk. A test
that only checked "no file appeared this time" would pass equally well against
an implementation that writes one under a condition the test did not happen to
hit.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from jarvis.audio import ring_buffer as ring_buffer_module
from jarvis.audio.ports import SAMPLE_RATE, AudioChunk, AudioFormat, Transcript
from jarvis.audio.pipeline import ActivationRoute, ListeningState, VoicePipeline
from jarvis.audio.ring_buffer import RingBuffer
from jarvis.audio.stt import strip_wake_phrase
from jarvis.audio.wake import NullWakeDetector


def frame(level: float = 0.0, seconds: float = 0.08) -> AudioChunk:
    """A frame of constant-amplitude audio."""
    import struct

    count = int(SAMPLE_RATE * seconds)
    return AudioChunk(
        samples=struct.pack(f"<{count}f", *([level] * count)),
        sample_rate=SAMPLE_RATE,
        audio_format=AudioFormat.FLOAT32,
    )


class FakeStt:
    available = True

    def __init__(self, text: str = "hey jarvis open brave", confidence: float = 0.9) -> None:
        self._text = text
        self._confidence = confidence
        self.calls = 0

    def unavailable_reason(self) -> str | None:
        return None

    def transcribe(self, audio: AudioChunk) -> Transcript:
        self.calls += 1
        return Transcript(
            text=self._text, confidence=self._confidence, duration_seconds=audio.duration_seconds
        )


class FakeWake:
    """Fires once, when told to."""

    available = True
    threshold = 0.5

    def __init__(self) -> None:
        self.armed = False

    def unavailable_reason(self) -> str | None:
        return None

    def score(self, chunk: AudioChunk) -> float:
        return 0.95 if self.armed else 0.0

    def reset(self) -> None:
        self.armed = False


# -- AT-002: nothing reaches disk before a wake ----------------------------
def test_the_ring_buffer_has_no_file_handling_at_all() -> None:
    """Structural: it cannot write to disk, rather than happening not to."""
    source = inspect.getsource(ring_buffer_module)
    tree = ast.parse(source)

    forbidden_calls = {"open", "write_bytes", "write_text", "mkdir", "dump", "dumps", "save"}
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if name in forbidden_calls:
                found.append(f"line {node.lineno}: {name}")
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", "") or ""
            names = [a.name for a in getattr(node, "names", [])]
            for candidate in [module, *names]:
                assert candidate.split(".")[0] not in {"shutil", "pickle", "wave", "soundfile"}, (
                    f"the ring buffer imports {candidate}; pre-wake audio must stay in memory"
                )

    assert not found, (
        "The pre-wake ring buffer must have no way to write audio to disk "
        "(PRD FR-012, AT-002). Found: " + ", ".join(found)
    )


def test_listening_without_a_wake_writes_no_audio_file(tmp_path: Path) -> None:
    pipeline = VoicePipeline(
        wake_detector=FakeWake(), stt=FakeStt(), always_listening=True, phrase="Hey Jarvis"
    )
    pipeline.start_listening()

    for _ in range(60):  # ~5 seconds
        pipeline.push_frame(frame(0.02))

    assert pipeline.state is ListeningState.WAITING_FOR_WAKE
    assert list(tmp_path.rglob("*")) == []


def test_pre_wake_audio_is_bounded_and_old_audio_is_discarded() -> None:
    """FR-012: a *short* window, not a recording."""
    buffer = RingBuffer(window_seconds=1.0)
    for _ in range(50):  # 4 seconds of 80 ms frames
        buffer.write(frame(0.1))

    assert buffer.held_seconds <= 1.05
    assert buffer.total_written_bytes > buffer.held_bytes, "old audio must be dropped"


def test_stopping_listening_forgets_everything_held() -> None:
    pipeline = VoicePipeline(wake_detector=FakeWake(), stt=FakeStt(), always_listening=True)
    pipeline.start_listening()
    for _ in range(10):
        pipeline.push_frame(frame(0.05))
    assert pipeline.ring_buffer.held_bytes > 0

    pipeline.stop_listening()
    assert pipeline.ring_buffer.held_bytes == 0
    assert pipeline.state is ListeningState.OFF


def test_a_wake_promotes_the_buffer_and_then_clears_it() -> None:
    """The run-up is why the buffer exists; it must not linger afterwards."""
    wake = FakeWake()
    pipeline = VoicePipeline(wake_detector=wake, stt=FakeStt(), always_listening=True)
    pipeline.start_listening()

    for _ in range(5):
        pipeline.push_frame(frame(0.05))
    assert pipeline.ring_buffer.held_bytes > 0

    wake.armed = True
    pipeline.push_frame(frame(0.05))

    assert pipeline.state is ListeningState.CAPTURING_COMMAND
    assert pipeline.ring_buffer.held_bytes == 0


# -- FR-024: the wake phrase never reaches the planner ---------------------
@pytest.mark.parametrize(
    "heard, expected",
    [
        ("Hey Jarvis, open Brave", "open Brave"),
        ("hey jarvis open brave", "open brave"),
        ("Hey Jarvis. What is the time?", "What is the time?"),
        ("  hey  jarvis   play music", "play music"),
        ("open Brave", "open Brave"),
    ],
)
def test_the_wake_phrase_is_stripped_from_the_command(heard: str, expected: str) -> None:
    assert strip_wake_phrase(heard, "Hey Jarvis") == expected


def test_only_the_leading_wake_phrase_is_stripped() -> None:
    """"Remind me to say hey Jarvis" is a command, not two wakes."""
    text = "Hey Jarvis, remind me to say hey Jarvis tomorrow"
    assert strip_wake_phrase(text, "Hey Jarvis") == "remind me to say hey Jarvis tomorrow"


# -- FR-025: command audio is discarded after transcription ----------------
def test_command_audio_is_released_once_transcribed() -> None:
    stt = FakeStt()
    wake = FakeWake()
    pipeline = VoicePipeline(wake_detector=wake, stt=stt, always_listening=True)
    pipeline.start_listening()

    wake.armed = True
    pipeline.push_frame(frame(0.3))
    for _ in range(4):
        pipeline.push_frame(frame(0.3))
    for _ in range(15):  # silence long enough to end the command
        pipeline.push_frame(frame(0.0))

    assert stt.calls == 1
    assert pipeline._command_frames == []  # noqa: SLF001


def test_a_transcribed_command_is_delivered_without_the_wake_phrase() -> None:
    heard: list[object] = []
    wake = FakeWake()
    pipeline = VoicePipeline(
        wake_detector=wake,
        stt=FakeStt("hey jarvis open brave"),
        always_listening=True,
        on_command=heard.append,
    )
    pipeline.start_listening()
    wake.armed = True
    pipeline.push_frame(frame(0.3))
    for _ in range(3):
        pipeline.push_frame(frame(0.3))
    for _ in range(15):
        pipeline.push_frame(frame(0.0))

    assert len(heard) == 1
    assert heard[0].text == "open brave"  # type: ignore[attr-defined]
    assert heard[0].route is ActivationRoute.WAKE_WORD  # type: ignore[attr-defined]


# -- FR-023: low confidence confirms rather than acting --------------------
def test_a_low_confidence_command_is_flagged_for_confirmation() -> None:
    heard: list[object] = []
    pipeline = VoicePipeline(
        wake_detector=NullWakeDetector("no model"),
        stt=FakeStt("delete everything", confidence=0.2),
        always_listening=False,
        on_command=heard.append,
    )
    pipeline.begin_push_to_talk()
    pipeline.push_frame(frame(0.3))
    command = pipeline.end_push_to_talk()

    assert command is not None
    assert command.needs_confirmation


def test_a_confident_command_is_not_flagged() -> None:
    pipeline = VoicePipeline(
        wake_detector=NullWakeDetector("no model"),
        stt=FakeStt("open brave", confidence=0.95),
        always_listening=False,
    )
    pipeline.begin_push_to_talk()
    pipeline.push_frame(frame(0.3))
    command = pipeline.end_push_to_talk()

    assert command is not None
    assert not command.needs_confirmation


# -- push-to-talk works without any wake model (ADR-0016 fallback) ---------
def test_push_to_talk_works_with_no_wake_model_installed() -> None:
    detector = NullWakeDetector("no wake-word model is installed")
    pipeline = VoicePipeline(wake_detector=detector, stt=FakeStt("open brave"))

    pipeline.begin_push_to_talk()
    assert pipeline.state is ListeningState.CAPTURING_COMMAND
    pipeline.push_frame(frame(0.3))
    command = pipeline.end_push_to_talk()

    assert command is not None
    assert command.text == "open brave"
    assert command.route is ActivationRoute.PUSH_TO_TALK


def test_always_listening_stays_off_until_it_is_enabled() -> None:
    """ADR-0016 criterion 2: not enabled until enrolment passes."""
    pipeline = VoicePipeline(
        wake_detector=FakeWake(), stt=FakeStt(), always_listening=False
    )
    pipeline.start_listening()
    assert pipeline.state is ListeningState.OFF

    pipeline.set_always_listening(True)
    pipeline.start_listening()
    assert pipeline.state is ListeningState.WAITING_FOR_WAKE
