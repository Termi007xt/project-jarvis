"""Interrupting Jarvis mid-sentence — why it never worked, and what fixed it.

Reported from real use: "i am not able to interrupt it for some reason." The
plumbing was never the problem — :func:`jarvis.audio.playback.play` polls
``should_stop`` every 40 ms. Nothing was reaching it, for two reasons that both
live in :mod:`jarvis.audio.duplex`.

**The raised threshold was unreachable.** ``PLAYBACK_SCORE_MULTIPLIER`` was 1.6
against a 0.6 base threshold, so a detection had to score 0.96 while Jarvis was
speaking. openWakeWord effectively never does, so defence 3 of ADR-0028 was not
a raised bar, it was a closed door.

**The echo comparison used two different units.** It measured our own *digital
output samples* with :meth:`note_emitted_level` and compared them against the
*microphone* level of the room, rejecting the detection when the microphone was
quieter. A desk microphone hearing a person across the room is almost always
quieter than the RMS of a synthesised waveform, so genuine interruptions were
rejected as self-echo essentially every time.

The comparison is meaningful only between like and like: what the microphone
hears while Jarvis speaks and nobody else does *is* the echo floor, and it is
measurable with the same instrument on the same scale.
"""

from __future__ import annotations

from jarvis.audio.duplex import (
    ECHO_MARGIN,
    PLAYBACK_SCORE_MULTIPLIER,
    DuplexCoordinator,
)
from jarvis.audio.ports import SAMPLE_RATE, AudioChunk, AudioFormat, WakeEvent
from jarvis.common import utc_now

#: The wake detector's shipped threshold. The arithmetic below is only
#: meaningful against the value actually in use.
BASE_THRESHOLD = 0.6


def _frame(level: float, seconds: float = 0.08) -> AudioChunk:
    import struct

    count = int(SAMPLE_RATE * seconds)
    return AudioChunk(
        samples=struct.pack(f"<{count}f", *([level] * count)),
        sample_rate=SAMPLE_RATE,
        audio_format=AudioFormat.FLOAT32,
    )


def _detection(score: float) -> WakeEvent:
    return WakeEvent(phrase="Hey Jarvis", score=score, detected_at=utc_now())


# -- defence 3 must be a raised bar, not a closed door ----------------------
def test_the_threshold_raised_during_playback_is_reachable() -> None:
    """At 1.6 this demanded 0.96, which openWakeWord does not produce."""
    required = BASE_THRESHOLD * PLAYBACK_SCORE_MULTIPLIER
    assert required <= 0.95, (
        f"a detection would have to score {required:.2f} to interrupt Jarvis; "
        "acoustic barge-in is unreachable at that bar"
    )
    assert PLAYBACK_SCORE_MULTIPLIER > 1.0, "the bar should still be raised"


def test_a_detection_below_the_raised_threshold_is_still_rejected() -> None:
    coordinator = DuplexCoordinator()
    coordinator.playback_started("a long answer")
    assert not coordinator.accept_detection(
        _detection(BASE_THRESHOLD), BASE_THRESHOLD, captured_level=0.5
    )


# -- the echo floor is measured with the same instrument --------------------
def test_a_real_interruption_at_a_realistic_microphone_level_is_accepted() -> None:
    """The case the old comparison rejected: quiet room, loud output."""
    coordinator = DuplexCoordinator()
    coordinator.playback_started("a long answer")
    coordinator.note_emitted_level(_frame(0.40))  # our samples, digital scale
    for _ in range(10):
        coordinator.note_captured_level(0.03)  # the room, microphone scale

    assert coordinator.accept_detection(
        _detection(0.75), BASE_THRESHOLD, captured_level=0.11
    )
    assert coordinator.accepted_during_playback_count == 1


def test_our_own_voice_coming_back_in_is_still_rejected() -> None:
    coordinator = DuplexCoordinator()
    coordinator.playback_started("Hey Jarvis is my own name")
    for _ in range(10):
        coordinator.note_captured_level(0.09)

    assert not coordinator.accept_detection(
        _detection(0.95), BASE_THRESHOLD, captured_level=0.10
    )
    assert coordinator.self_trigger_count == 1


def test_the_floor_ignores_how_loud_our_own_samples_were() -> None:
    """A loud synthesised waveform must not raise the bar for the user."""
    coordinator = DuplexCoordinator()
    coordinator.playback_started("x")
    coordinator.note_emitted_level(_frame(0.95))
    coordinator.note_captured_level(0.02)

    assert coordinator.accept_detection(
        _detection(0.80), BASE_THRESHOLD, captured_level=0.20
    )


def test_the_margin_over_the_floor_is_a_margin_not_a_wall() -> None:
    assert 1.0 < ECHO_MARGIN <= 2.0


def test_the_echo_floor_starts_again_for_each_utterance() -> None:
    """A shout during one reply must not deafen Jarvis for the next."""
    coordinator = DuplexCoordinator()
    coordinator.playback_started("first")
    coordinator.note_captured_level(0.60)
    coordinator.playback_finished()

    coordinator.playback_started("second")
    coordinator.note_captured_level(0.02)
    assert coordinator.accept_detection(
        _detection(0.80), BASE_THRESHOLD, captured_level=0.15
    )


def test_a_detection_with_no_floor_measured_yet_is_judged_on_score_alone() -> None:
    """Playback has only just begun; there is nothing to compare against."""
    coordinator = DuplexCoordinator()
    coordinator.playback_started("x")
    assert coordinator.accept_detection(
        _detection(0.80), BASE_THRESHOLD, captured_level=0.01
    )


def test_a_detection_while_silent_is_never_second_guessed() -> None:
    coordinator = DuplexCoordinator()
    assert coordinator.accept_detection(
        _detection(BASE_THRESHOLD), BASE_THRESHOLD, captured_level=0.001
    )


# -- what the Voice screen is allowed to claim ------------------------------
def test_it_does_not_claim_you_can_interrupt_with_the_microphone_closed() -> None:
    """Full duplex plus a closed microphone is not an interruptible Jarvis."""
    description = DuplexCoordinator().describe_interruption(
        listening=False, hotkey="Ctrl+Alt+End"
    )
    assert "will not interrupt" in description
    assert "Ctrl+Alt+End" in description


def test_it_names_the_keyboard_route_in_every_state() -> None:
    from jarvis.audio.duplex import DuplexMode

    for mode in (DuplexMode.FULL, DuplexMode.HALF):
        for listening in (True, False):
            description = DuplexCoordinator(mode=mode).describe_interruption(
                listening=listening, hotkey="Ctrl+Alt+End"
            )
            assert "Ctrl+Alt+End" in description
            assert "Stop speaking" in description


def test_it_does_not_claim_a_self_trigger_rate_it_has_not_measured() -> None:
    description = DuplexCoordinator().describe_interruption(
        listening=True, hotkey="Ctrl+Alt+End"
    )
    assert "not measured" in description


# -- the pipeline feeds the floor ------------------------------------------
def test_the_pipeline_measures_the_room_while_jarvis_speaks() -> None:
    """Without this the floor stays at zero and the defence does nothing."""
    from jarvis.audio.pipeline import VoicePipeline

    class _Wake:
        available = True
        threshold = BASE_THRESHOLD

        def score(self, chunk: AudioChunk) -> float:
            return 0.0

        def reset(self) -> None:
            return None

    pipeline = VoicePipeline(wake_detector=_Wake(), stt=object(), always_listening=True)
    pipeline.start_listening()
    pipeline.speaking_started("a long answer")
    for _ in range(5):
        pipeline.push_frame(_frame(0.2))

    assert pipeline.duplex.echo_floor > 0.0, "nothing measured the room during playback"
