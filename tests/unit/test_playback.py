"""Audio playback, and the honesty rule that depends on it (FR-030, FR-048).

Playback did not exist. ``voice.speak`` synthesised audio, nothing played it,
and the tool reported "Spoken." as a *verified* success. These tests pin both
halves: that playback reports what it really did, and that the tool refuses to
claim speech it cannot evidence.

Nothing here opens a real output device — the sounddevice module is replaced, so
these run on CI and on a machine with no speakers.
"""

from __future__ import annotations

import sys
import types

import pytest

from jarvis.audio.playback import (
    BLOCK_MILLISECONDS,
    PlaybackReport,
    play,
    playback_available,
    playback_unavailable_reason,
)
from jarvis.audio.ports import AudioChunk, AudioFormat


def _silence(seconds: float = 0.5, rate: int = 24_000) -> AudioChunk:
    numpy = pytest.importorskip("numpy")
    samples = numpy.zeros(int(rate * seconds), dtype=numpy.float32)
    return AudioChunk(samples=samples.tobytes(), sample_rate=rate)


class FakeStream:
    """Records what was written, like a speaker that keeps receipts."""

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.written: list[int] = []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.closed = True

    def write(self, block) -> None:
        self.written.append(len(block))


@pytest.fixture
def fake_sounddevice(monkeypatch):
    """Stand in for the real library so no device is opened."""
    module = types.ModuleType("sounddevice")
    created: list[FakeStream] = []

    def OutputStream(**kwargs):  # noqa: N802 - mirrors the real API
        stream = FakeStream(**kwargs)
        created.append(stream)
        return stream

    module.OutputStream = OutputStream  # type: ignore[attr-defined]
    module.default = types.SimpleNamespace(device=(1, 2))  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sounddevice", module)
    module.created = created  # type: ignore[attr-defined]
    return module


pytestmark = pytest.mark.skipif(
    not playback_available(), reason="playback needs sounddevice and numpy"
)


# -- reporting what actually happened --------------------------------------
def test_playing_audio_reports_the_seconds_that_were_played(fake_sounddevice) -> None:
    report = play(_silence(0.5))
    assert report.played
    assert report.seconds == pytest.approx(0.5, abs=0.05)
    assert not report.interrupted
    assert report.error is None


def test_empty_audio_is_not_reported_as_played() -> None:
    report = play(AudioChunk(samples=b"", sample_rate=24_000))
    assert not report.played
    assert report.seconds == 0.0
    assert report.error


def test_a_dead_output_device_is_reported_not_raised(monkeypatch, fake_sounddevice) -> None:
    """A tool must get an answer, not an exception it cannot describe."""

    def explode(**kwargs):
        raise OSError("no output device")

    fake_sounddevice.OutputStream = explode
    report = play(_silence(0.2))
    assert not report.played
    assert "no output device" in (report.error or "")


def test_the_stream_is_always_closed(fake_sounddevice) -> None:
    play(_silence(0.2))
    assert fake_sounddevice.created[0].closed


# -- barge-in (ADR-0028) ----------------------------------------------------
def test_playback_stops_when_asked_to(fake_sounddevice) -> None:
    """The coordinator documents this flag as polled between buffers."""
    report = play(_silence(5.0), should_stop=lambda: True)
    assert report.interrupted
    assert report.seconds == 0.0


def test_playback_stops_part_way_through(fake_sounddevice) -> None:
    calls = {"n": 0}

    def should_stop() -> bool:
        calls["n"] += 1
        return calls["n"] > 3

    report = play(_silence(5.0), should_stop=should_stop)
    assert report.interrupted
    assert 0.0 < report.seconds < 5.0


def test_interruption_latency_is_one_block(fake_sounddevice) -> None:
    """Worst-case barge-in latency is the block size, so it must stay short."""
    assert BLOCK_MILLISECONDS <= 50


def test_uninterrupted_playback_is_not_marked_interrupted(fake_sounddevice) -> None:
    report = play(_silence(0.3), should_stop=lambda: False)
    assert not report.interrupted
    assert report.played


# -- what the duplex coordinator needs -------------------------------------
def test_emitted_audio_is_offered_back_for_echo_attribution(fake_sounddevice) -> None:
    """ADR-0028 compares our own output level against what the mic hears."""
    seen: list[AudioChunk] = []
    play(_silence(0.4), on_block=seen.append)
    assert seen, "playback never reported what it emitted"
    assert all(chunk.audio_format is AudioFormat.FLOAT32 for chunk in seen)


# -- bounds -----------------------------------------------------------------
def test_playback_is_bounded(fake_sounddevice) -> None:
    """Every external interaction declares a bound (CLAUDE.md)."""
    report = play(_silence(30.0), max_seconds=1.0)
    assert report.seconds == pytest.approx(1.0, abs=0.1)


# -- pcm16 input ------------------------------------------------------------
def test_pcm16_audio_plays_too(fake_sounddevice) -> None:
    numpy = pytest.importorskip("numpy")
    samples = numpy.zeros(24_000, dtype=numpy.int16)
    chunk = AudioChunk(
        samples=samples.tobytes(), sample_rate=24_000, audio_format=AudioFormat.PCM16
    )
    report = play(chunk)
    assert report.played


# -- describing itself ------------------------------------------------------
def test_a_report_describes_itself_honestly() -> None:
    assert "nothing was played" in PlaybackReport(played=False, seconds=0.0).describe()
    assert "interrupted" in PlaybackReport(played=True, seconds=1.0, interrupted=True).describe()
    assert "played" in PlaybackReport(played=True, seconds=2.0).describe()
    assert "boom" in PlaybackReport(played=False, seconds=0.0, error="boom").describe()


def test_unavailable_playback_explains_itself(monkeypatch) -> None:
    monkeypatch.setattr("jarvis.audio.playback.module_available", lambda name: False)
    reason = playback_unavailable_reason()
    assert reason and "sounddevice" in reason
