"""Opening the microphone must match the device's host API (PRD FR-016).

Windows exposes one physical microphone through four host APIs — MME,
DirectSound, WASAPI and WDM-KS — under near-identical names. They do not accept
the same stream settings, and getting it wrong is not a degradation: the stream
does not open at all.

The defect: `WasapiSettings` was passed to every device. On the reporting
machine the system default input was an MME device, so **every** microphone open
failed with "Incompatible host API specific stream info" (PaErrorCode -9984).
Push-to-talk, the microphone test and calibration were all dead, and the Voice
screen listed the same microphone four times with no way to tell them apart.

Measured on that hardware:

    device 17 (WASAPI)       with WasapiSettings OK   · without: invalid sample rate
    device  1 (MME)          with WasapiSettings FAIL · without: OK
    device  8 (DirectSound)  with WasapiSettings FAIL · without: OK
"""

from __future__ import annotations

import sys
import types

import pytest

from jarvis.audio.capture import (
    WASAPI,
    CaptureSession,
    _same_microphone,
    default_input_device,
    list_devices,
)
from jarvis.audio.ports import AudioUnavailable

#: The device table from the machine that reported the defect.
DEVICES = [
    {"name": "Microsoft Sound Mapper - Input", "hostapi": 0, "max_input_channels": 2, "max_output_channels": 0, "default_samplerate": 44100.0},
    {"name": "Microphone (Maono AI Microphone", "hostapi": 0, "max_input_channels": 2, "max_output_channels": 0, "default_samplerate": 44100.0},
    {"name": "Microphone (Maono AI Microphone)", "hostapi": 1, "max_input_channels": 2, "max_output_channels": 0, "default_samplerate": 44100.0},
    {"name": "Microphone (Maono AI Microphone)", "hostapi": 2, "max_input_channels": 2, "max_output_channels": 0, "default_samplerate": 48000.0},
    {"name": "Microphone (Realtek HD Audio Mic input)", "hostapi": 3, "max_input_channels": 2, "max_output_channels": 0, "default_samplerate": 48000.0},
]
HOST_APIS = [{"name": "MME"}, {"name": "Windows DirectSound"}, {"name": WASAPI}, {"name": "Windows WDM-KS"}]

WASAPI_DEVICE = 3
MME_DEFAULT = 1


class _WasapiSettings:
    def __init__(self, auto_convert: bool = False) -> None:
        self.auto_convert = auto_convert


class FakeSounddevice(types.ModuleType):
    """Refuses the wrong settings exactly as PortAudio does."""

    def __init__(self) -> None:
        super().__init__("sounddevice")
        self.default = types.SimpleNamespace(device=(MME_DEFAULT, 5))
        self.WasapiSettings = _WasapiSettings
        self.opened: list[tuple[int | None, bool]] = []

    def query_devices(self, index=None):
        return DEVICES if index is None else DEVICES[index]

    def query_hostapis(self, index=None):
        return HOST_APIS if index is None else HOST_APIS[index]

    def InputStream(self, **kwargs):  # noqa: N802 - mirrors the real API
        index = kwargs.get("device")
        extra = kwargs.get("extra_settings")
        self.opened.append((index, extra is not None))
        resolved = self.default.device[0] if index is None else index
        is_wasapi = DEVICES[resolved]["hostapi"] == 2
        if is_wasapi and extra is None:
            raise RuntimeError("Error opening InputStream: Invalid sample rate [PaErrorCode -9997]")
        if not is_wasapi and extra is not None:
            raise RuntimeError(
                "Error opening InputStream: Incompatible host API specific stream info [PaErrorCode -9984]"
            )
        return types.SimpleNamespace(start=lambda: None, stop=lambda: None, close=lambda: None)


@pytest.fixture
def fake_sounddevice(monkeypatch):
    module = FakeSounddevice()
    monkeypatch.setitem(sys.modules, "sounddevice", module)
    monkeypatch.setattr("jarvis.audio.capture.capture_available", lambda: True)
    return module


# -- the defect -------------------------------------------------------------
@pytest.mark.parametrize("device_index", [0, MME_DEFAULT, 2, WASAPI_DEVICE, None])
def test_the_microphone_opens_on_every_host_api(fake_sounddevice, device_index) -> None:
    """It opened on none of them: the settings never matched the device."""
    session = CaptureSession(device_index=device_index).start()
    assert session.running
    session.stop()


def test_a_wasapi_device_is_opened_with_voice_capture_processing(fake_sounddevice) -> None:
    """ADR-0028 defence 2 — echo cancellation is why WASAPI is preferred."""
    CaptureSession(device_index=WASAPI_DEVICE).start().stop()
    assert fake_sounddevice.opened[0] == (WASAPI_DEVICE, True), (
        "the first attempt on a WASAPI device must carry WasapiSettings"
    )


def test_a_non_wasapi_device_is_not_given_wasapi_settings_first(fake_sounddevice) -> None:
    CaptureSession(device_index=MME_DEFAULT).start().stop()
    assert fake_sounddevice.opened[0] == (MME_DEFAULT, False)


def test_a_device_that_cannot_open_at_all_says_so(fake_sounddevice, monkeypatch) -> None:
    def always_fail(**kwargs):
        raise RuntimeError("Unanticipated host error [PaErrorCode -9999]")

    monkeypatch.setattr(fake_sounddevice, "InputStream", always_fail)
    with pytest.raises(AudioUnavailable, match="could not be opened"):
        CaptureSession(device_index=4).start()


def test_a_failed_open_leaves_no_recording_indicator_lit(fake_sounddevice, monkeypatch) -> None:
    """FR-013 in reverse: the indicator must not survive a failed start."""
    states: list[bool] = []

    def always_fail(**kwargs):
        raise RuntimeError("nope")

    monkeypatch.setattr(fake_sounddevice, "InputStream", always_fail)
    with pytest.raises(AudioUnavailable):
        CaptureSession(device_index=4, indicator=states.append).start()
    assert states[-1] is False if states else True


# -- choosing the right entry ----------------------------------------------
def test_the_wasapi_variant_wins_over_the_system_default(fake_sounddevice) -> None:
    """Windows' default was MME, which gives no echo cancellation."""
    chosen = default_input_device()
    assert chosen is not None
    assert chosen.index == WASAPI_DEVICE
    assert chosen.host_api == WASAPI


def test_devices_are_distinguishable_in_the_list(fake_sounddevice) -> None:
    """Four identically-named entries are not a choice a user can make."""
    described = [device.describe() for device in list_devices(inputs_only=True)]
    assert len(set(described)) == len(described), f"duplicate entries: {described}"
    assert any(WASAPI in text for text in described)


def test_matching_the_same_microphone_across_host_apis() -> None:
    """MME truncates names, so an exact comparison never matches."""
    assert _same_microphone("Microphone (Maono AI Microphone", "Microphone (Maono AI Microphone)")
    assert not _same_microphone("Microphone (Maono AI Microphone)", "Line In (Realtek)")
    assert not _same_microphone("", "anything")
