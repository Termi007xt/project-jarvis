"""Full-duplex audio, barge-in, TTS and STT (ADR-0028, PRD FR-015, 10.3, 10.4).

The four assertions ADR-0028 names under "Enforcement" are here, plus the
provider round trips against recorded fixtures. Nothing requires a microphone,
a GPU or the network.
"""

from __future__ import annotations

import struct

import pytest

from jarvis.audio.duplex import DuplexCoordinator, DuplexMode
from jarvis.audio.ports import SAMPLE_RATE, AudioChunk, AudioFormat, Transcript, WakeEvent
from jarvis.audio.pipeline import ListeningState, VoicePipeline
from jarvis.audio.tts import (
    NullTtsProvider,
    build_tts_provider,
    redact_for_speech,
)
from jarvis.audio.stt import CONFIRMATION_THRESHOLD, build_stt_provider, needs_confirmation
from jarvis.audio.vad import SpeechState, VoiceActivityDetector, calibrate, rms_level
from jarvis.common import utc_now


def frame(level: float = 0.0, seconds: float = 0.08) -> AudioChunk:
    count = int(SAMPLE_RATE * seconds)
    return AudioChunk(
        samples=struct.pack(f"<{count}f", *([level] * count)),
        sample_rate=SAMPLE_RATE,
        audio_format=AudioFormat.FLOAT32,
    )


class FakeStt:
    available = True

    def unavailable_reason(self) -> str | None:
        return None

    def transcribe(self, audio: AudioChunk) -> Transcript:
        return Transcript(text="open brave", confidence=0.9)


class LoudWake:
    available = True
    threshold = 0.5

    def __init__(self, score: float = 0.95) -> None:
        self._score = score

    def unavailable_reason(self) -> str | None:
        return None

    def score(self, chunk: AudioChunk) -> float:
        return self._score

    def reset(self) -> None:
        return None


# -- ADR-0028: playback does not stop capture ------------------------------
def test_starting_playback_does_not_stop_capture() -> None:
    coordinator = DuplexCoordinator()
    coordinator.playback_started("I am speaking now")
    assert coordinator.speaking
    assert coordinator.capture_should_run(), "full duplex means the microphone stays open"
    assert coordinator.detection_enabled()


def test_the_pipeline_keeps_taking_frames_while_speaking() -> None:
    pipeline = VoicePipeline(
        wake_detector=LoudWake(score=0.0), stt=FakeStt(), always_listening=True
    )
    pipeline.start_listening()
    pipeline.speaking_started("a long sentence")

    before = pipeline.ring_buffer.total_written_bytes
    for _ in range(5):
        pipeline.push_frame(frame(0.02))
    assert pipeline.ring_buffer.total_written_bytes > before


# -- ADR-0028: a self-echo does not trigger a wake -------------------------
def test_a_detection_attributed_to_our_own_output_is_rejected() -> None:
    """The synthetic self-echo case ADR-0028 requires.

    The baseline changed deliberately: it used to be the RMS of the samples
    Jarvis *emitted*, which is not on the same scale as a microphone level and
    rejected genuine interruptions almost every time. It is now what the
    microphone itself heard during playback (see tests/unit/test_interruption).
    """
    coordinator = DuplexCoordinator()
    window = coordinator.playback_started("Jarvis speaking")
    coordinator.note_emitted_level(frame(0.4))
    coordinator.note_captured_level(0.4)

    echo = WakeEvent(phrase="Hey Jarvis", score=0.6, detected_at=utc_now())
    # A score that would pass normally, no louder than the room already was.
    assert not coordinator.accept_detection(echo, 0.5, captured_level=0.38)
    assert coordinator.self_trigger_count == 1
    assert window.peak_level > 0


def test_a_genuine_interruption_during_playback_is_accepted() -> None:
    coordinator = DuplexCoordinator()
    coordinator.playback_started("Jarvis speaking")
    coordinator.note_emitted_level(frame(0.1))

    user = WakeEvent(phrase="Hey Jarvis", score=0.98, detected_at=utc_now())
    assert coordinator.accept_detection(user, 0.5, captured_level=0.9)
    assert coordinator.accepted_during_playback_count == 1


def test_a_detection_while_silent_is_not_second_guessed() -> None:
    coordinator = DuplexCoordinator()
    event = WakeEvent(phrase="Hey Jarvis", score=0.55, detected_at=utc_now())
    assert coordinator.accept_detection(event, 0.5, captured_level=0.5)


def test_a_detection_just_after_playback_still_counts_as_overlapping() -> None:
    """Sound takes time to travel; the echo tail is not zero."""
    coordinator = DuplexCoordinator()
    coordinator.playback_started("x")
    coordinator.note_captured_level(0.4)
    coordinator.playback_finished()

    echo = WakeEvent(phrase="Hey Jarvis", score=0.6, detected_at=utc_now())
    assert not coordinator.accept_detection(echo, 0.5, captured_level=0.38)


# -- ADR-0028: barge-in stops speech and nothing else ----------------------
def test_barge_in_stops_playback_but_releases_no_locks_and_cancels_no_tasks() -> None:
    """Conflating this with emergency stop would make "stop talking" destructive."""
    coordinator = DuplexCoordinator()
    coordinator.playback_started("a long answer")

    report = coordinator.request_barge_in("the user spoke")
    assert report.interrupted
    assert coordinator.stop_requested
    assert report.released_locks == ()
    assert report.cancelled_tasks == ()


def test_barge_in_when_nothing_is_playing_is_harmless() -> None:
    coordinator = DuplexCoordinator()
    report = coordinator.request_barge_in()
    assert not report.interrupted
    assert "not speaking" in report.reason


def test_push_to_talk_interrupts_speech_deterministically() -> None:
    """ADR-0028 keeps push-to-talk as the reliable interruption path."""
    pipeline = VoicePipeline(wake_detector=LoudWake(0.0), stt=FakeStt())
    pipeline.speaking_started("a long answer")
    pipeline.begin_push_to_talk()

    assert pipeline.duplex.stop_requested
    assert pipeline.state is ListeningState.CAPTURING_COMMAND


# -- the honest half-duplex fallback (ADR-0028, NFR-014) -------------------
def test_half_duplex_pauses_detection_while_speaking_and_says_so() -> None:
    coordinator = DuplexCoordinator(mode=DuplexMode.HALF)
    coordinator.playback_started("speaking")

    assert not coordinator.detection_enabled()
    assert "cannot interrupt by voice" in coordinator.describe_mode()
    assert "push-to-talk" in coordinator.describe_mode()


def test_full_duplex_describes_itself_differently() -> None:
    assert "interrupt" in DuplexCoordinator().describe_mode()


def test_the_measurement_that_gates_enabling_barge_in_is_reported() -> None:
    coordinator = DuplexCoordinator()
    assert "No detections" in coordinator.measurement_summary()

    coordinator.playback_started("x")
    coordinator.note_captured_level(0.4)
    coordinator.accept_detection(
        WakeEvent(phrase="p", score=0.6, detected_at=utc_now()), 0.5, captured_level=0.38
    )
    assert "1 of 1" in coordinator.measurement_summary()


# -- voice activity detection (FR-014, FR-017) -----------------------------
def test_speech_starts_and_ends_around_silence() -> None:
    detector = VoiceActivityDetector(hangover_seconds=0.3)
    assert detector.push(frame(0.0)) is SpeechState.SILENT

    for _ in range(3):
        detector.push(frame(0.5))
    assert detector.state is SpeechState.SPEAKING

    for _ in range(6):
        detector.push(frame(0.0))
    assert detector.state is SpeechState.ENDED
    assert detector.ended_because == "silence"


def test_a_brief_pause_does_not_end_the_command() -> None:
    """People pause mid-sentence; cutting there truncates the command."""
    detector = VoiceActivityDetector(hangover_seconds=0.8)
    for _ in range(3):
        detector.push(frame(0.5))
    for _ in range(3):  # 240 ms of quiet
        detector.push(frame(0.0))
    assert detector.state is SpeechState.SPEAKING


def test_a_command_cannot_run_forever() -> None:
    detector = VoiceActivityDetector(max_command_seconds=0.5, hangover_seconds=5.0)
    for _ in range(20):
        detector.push(frame(0.5))
    assert detector.state is SpeechState.ENDED
    assert "limit" in detector.ended_because


def test_calibration_raises_the_threshold_in_a_noisy_room() -> None:
    quiet = calibrate([frame(0.001) for _ in range(10)])
    noisy = calibrate([frame(0.05) for _ in range(10)])
    assert noisy.speech_threshold > quiet.speech_threshold
    assert quiet.describe()


def test_calibration_with_no_frames_still_gives_a_usable_threshold() -> None:
    assert calibrate([]).speech_threshold > 0


def test_the_level_meter_reflects_loudness() -> None:
    assert rms_level(frame(0.0)) == pytest.approx(0.0, abs=1e-6)
    assert rms_level(frame(0.5)) > rms_level(frame(0.1))


# -- text to speech (FR-030 to FR-034) -------------------------------------
def test_the_configured_provider_is_built_from_configuration(config) -> None:
    provider = build_tts_provider(config)
    assert provider.voices() or provider.unavailable_reason()


def test_every_voice_carries_licence_metadata(config) -> None:
    """FR-032: nothing may be shipped on the assumption a licence was fine."""
    provider = build_tts_provider(config)
    for voice in provider.voices():
        assert voice.licence
        assert voice.redistributable is False, (
            "ADR-0014 left public redistribution unresolved; no voice may claim it"
        )
        assert "licence" in voice.describe()


@pytest.mark.parametrize(
    "text, label",
    [
        ("My key is sk-live-abcdefghijklmnop", "a key"),
        ("Email me at someone@example.com", "an email address"),
        ("The code is 483920", "a verification code"),
        ("Card 4111 1111 1111 1111", "a card number"),
    ],
)
def test_sensitive_text_is_never_spoken_aloud(text: str, label: str) -> None:
    """FR-034: speaking a password is not recoverable by apologising."""
    spoken, redacted = redact_for_speech(text)
    assert redacted
    assert label in spoken
    assert "sk-live-abcdefghijklmnop" not in spoken
    assert "483920" not in spoken


def test_ordinary_text_is_spoken_unchanged() -> None:
    spoken, redacted = redact_for_speech("Brave is open and YouTube is playing.")
    assert not redacted
    assert spoken == "Brave is open and YouTube is playing."


def test_an_unavailable_voice_refuses_rather_than_pretending() -> None:
    from jarvis.audio.ports import AudioUnavailable

    provider = NullTtsProvider("Kokoro is not installed")
    assert not provider.available
    with pytest.raises(AudioUnavailable):
        provider.synthesise("hello")


# -- speech to text (FR-020 to FR-023) -------------------------------------
def test_the_configured_recogniser_is_built_from_configuration(config) -> None:
    provider = build_stt_provider(config)
    assert provider.available or provider.unavailable_reason()


def test_the_configured_settings_match_the_verified_spike(config) -> None:
    """Ported from tools/voice-lab, not re-guessed."""
    settings = config.audio.speech_to_text
    assert settings.model == "small"
    assert settings.device == "cpu"
    assert settings.compute_type == "int8"
    assert settings.beam_size == 1
    assert settings.vad_filter is True
    assert settings.retain_raw_audio is False


def test_a_transcript_with_no_confidence_is_treated_as_uncertain() -> None:
    """Unknown is not the same as high."""
    assert needs_confirmation(Transcript(text="delete everything", confidence=None))


def test_an_empty_transcript_needs_no_confirmation() -> None:
    assert not needs_confirmation(Transcript(text="   ", confidence=None))


def test_the_confirmation_threshold_is_the_documented_one() -> None:
    assert needs_confirmation(
        Transcript(text="x", confidence=CONFIRMATION_THRESHOLD - 0.01)
    )
    assert not needs_confirmation(
        Transcript(text="x", confidence=CONFIRMATION_THRESHOLD + 0.01)
    )
