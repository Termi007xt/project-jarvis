"""``voice.speak`` must not claim speech it cannot evidence (FR-048, AT-018).

The defect: the tool returned ``verification=VERIFIED`` and the message
"Spoken." as soon as synthesis produced audio. Nothing played that audio —
there was no playback code anywhere in the product — so every "Spoken." was a
confirmed success for a silent room.

That is precisely the failure mode FR-048 exists to prevent, and it is worse
than a crash because the transcript then carries a tool-confirmed label.
"""

from __future__ import annotations

import pytest

from jarvis.audio.playback import PlaybackReport
from jarvis.audio.ports import AudioChunk, AudioFormat
from jarvis.audio.service import SpokenResult
from jarvis.core.tools.contract import ToolContext, ToolFailure, Verification
from jarvis.toolbox.phase1_tools import SpeakTool


def _audio(seconds: float = 1.0) -> AudioChunk:
    # 24 kHz float32 mono, as Kokoro produces.
    return AudioChunk(
        samples=b"\x00\x00\x00\x00" * int(24_000 * seconds),
        sample_rate=24_000,
        audio_format=AudioFormat.FLOAT32,
    )


def _spoken(**overrides) -> SpokenResult:
    defaults = dict(
        audio=_audio(),
        voice_id="bm_george",
        text="hello",
        redacted=False,
        playback=PlaybackReport(played=True, seconds=1.0),
    )
    defaults.update(overrides)
    return SpokenResult(**defaults)  # type: ignore[arg-type]


def _run(result: object):
    tool = SpeakTool(lambda text: result)
    parameters = SpeakTool.spec.input_model(text="hello")
    return tool.run(ToolContext(), parameters)


# -- the defect -------------------------------------------------------------
def test_audio_that_was_never_played_is_a_failure_not_a_success() -> None:
    """Synthesising is not speaking."""
    with pytest.raises(ToolFailure) as caught:
        _run(_spoken(playback=PlaybackReport(played=False, seconds=0.0, error="no device")))
    assert caught.value.code == "playback_failed"
    assert "no device" in caught.value.message


def test_a_result_with_no_playback_evidence_is_refused() -> None:
    """A bare synthesis result carries no evidence anything was heard."""

    class OldStyleResult:
        audio = _audio()
        voice_id = "bm_george"
        redacted = False

    with pytest.raises(ToolFailure) as caught:
        _run(OldStyleResult())
    assert caught.value.code == "playback_failed"


def test_no_voice_at_all_is_reported_as_unavailable() -> None:
    with pytest.raises(ToolFailure) as caught:
        _run(None)
    assert caught.value.code == "voice_unavailable"


# -- the honest success -----------------------------------------------------
def test_audio_that_really_played_is_verified() -> None:
    execution = _run(_spoken(playback=PlaybackReport(played=True, seconds=1.4)))
    assert execution.verification is Verification.VERIFIED
    assert execution.output.spoken
    assert execution.output.seconds == 1.4
    assert "1.4s" in execution.message


def test_the_reported_duration_is_what_played_not_what_was_synthesised() -> None:
    """A five-second utterance cut off after one second lasted one second."""
    execution = _run(
        _spoken(
            audio=_audio(5.0),
            playback=PlaybackReport(played=True, seconds=1.0, interrupted=True),
        )
    )
    assert execution.output.seconds == 1.0


def test_an_interruption_is_described_as_one() -> None:
    execution = _run(
        _spoken(playback=PlaybackReport(played=True, seconds=0.8, interrupted=True))
    )
    assert "interrupted" in execution.message.lower()


def test_redaction_is_still_announced(monkeypatch) -> None:
    """FR-034: say something was withheld rather than quietly changing it."""
    execution = _run(_spoken(redacted=True))
    assert execution.output.redacted
    assert "removed" in execution.message.lower()


# -- the declared contract --------------------------------------------------
def test_every_failure_code_the_tool_raises_is_declared() -> None:
    """The invoker rejects an undeclared code, so this must stay in step."""
    assert "playback_failed" in SpeakTool.spec.failure_codes
    assert "voice_unavailable" in SpeakTool.spec.failure_codes


def test_the_spec_describes_verification_in_terms_of_playback() -> None:
    assert "output device" in SpeakTool.spec.verification
