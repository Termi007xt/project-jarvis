"""Microphone capture and playback (PRD FR-016, FR-013, ADR-0028).

``sounddevice`` is imported inside the functions that need it, never at module
scope, so this module is importable with no voice extra installed and the Voice
screen can explain what is missing (ADR-0010, NFR-014).

Two things here are requirements rather than conveniences:

* **The recording indicator** (FR-013). Capture is not allowed to start without
  announcing itself; :class:`CaptureSession` calls the indicator on start and
  stop, and the tray reflects it. "Recording without a visible indicator" is a
  *prohibited* capability in the catalogue, so this is a policy boundary and not
  a UI nicety.
* **Windows voice-capture processing** is requested at the device (ADR-0028
  defence 2). Using the platform's acoustic echo cancellation is strongly
  preferred to writing one, and it has to be asked for when the stream opens.
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, Iterator

from jarvis.audio.availability import VOICE_EXTRA_HINT, module_available
from jarvis.audio.ports import (
    FRAME_MILLISECONDS,
    SAMPLE_RATE,
    AudioChunk,
    AudioDevice,
    AudioFormat,
    AudioUnavailable,
)

__all__ = [
    "list_devices",
    "default_input_device",
    "CaptureSession",
    "capture_available",
    "WASAPI",
]

_LOG = logging.getLogger(__name__)

FRAME_SAMPLES = SAMPLE_RATE * FRAME_MILLISECONDS // 1000

#: Windows exposes the same physical microphone through four host APIs, and they
#: do not accept the same stream settings. WASAPI is the one that offers voice
#: capture processing (ADR-0028 defence 2), and it is also the only one that
#: accepts 16 kHz here — the others reject it unless PortAudio resamples for us.
WASAPI = "Windows WASAPI"


def capture_available() -> bool:
    return module_available("sounddevice") and module_available("numpy")


def _require_sounddevice():
    if not capture_available():
        raise AudioUnavailable(
            f"audio capture needs sounddevice and numpy; {VOICE_EXTRA_HINT}"
        )
    import sounddevice  # noqa: PLC0415 - lazy by design

    return sounddevice


def host_api_names() -> tuple[str, ...]:
    """Host API names by index, or empty if they cannot be read."""
    if not capture_available():
        return ()
    try:
        sounddevice = _require_sounddevice()
        return tuple(str(api.get("name", "")) for api in sounddevice.query_hostapis())
    except Exception:  # noqa: BLE001 - never break a screen over this
        _LOG.exception("could not enumerate audio host APIs")
        return ()


def list_devices(*, inputs_only: bool = False) -> tuple[AudioDevice, ...]:
    """Enumerate devices for the Voice screen (PRD FR-016). Never raises."""
    if not capture_available():
        return ()
    try:
        sounddevice = _require_sounddevice()
        default_in, default_out = sounddevice.default.device
        apis = host_api_names()
        devices: list[AudioDevice] = []
        for index, raw in enumerate(sounddevice.query_devices()):
            is_input = int(raw.get("max_input_channels", 0)) > 0
            is_output = int(raw.get("max_output_channels", 0)) > 0
            if inputs_only and not is_input:
                continue
            if not is_input and not is_output:
                continue
            api_index = int(raw.get("hostapi", -1))
            devices.append(
                AudioDevice(
                    index=index,
                    name=str(raw.get("name", f"device {index}")),
                    channels=int(
                        raw.get("max_input_channels" if is_input else "max_output_channels", 0)
                    ),
                    default_sample_rate=float(raw.get("default_samplerate", SAMPLE_RATE)),
                    is_input=is_input,
                    is_default=index in (default_in, default_out),
                    # Without this the same microphone appears three or four
                    # times under identical names and the user cannot tell which
                    # entry will actually open.
                    host_api=apis[api_index] if 0 <= api_index < len(apis) else "",
                )
            )
        return tuple(devices)
    except Exception:  # noqa: BLE001 - enumeration must never break a screen
        _LOG.exception("could not enumerate audio devices")
        return ()


def default_input_device() -> AudioDevice | None:
    """The best input to open, preferring WASAPI over the system default.

    Windows reports its default input under MME, which rejects the settings
    that give us echo cancellation and does not accept 16 kHz directly. When
    the same microphone is also present under WASAPI, that entry is the better
    one to open by every measure, so it wins.
    """
    inputs = list_devices(inputs_only=True)
    if not inputs:
        return None

    system_default = next((device for device in inputs if device.is_default), None)
    if system_default is not None and system_default.host_api != WASAPI:
        same_microphone = next(
            (
                device
                for device in inputs
                if device.host_api == WASAPI
                and _same_microphone(device.name, system_default.name)
            ),
            None,
        )
        if same_microphone is not None:
            return same_microphone
    if system_default is not None and system_default.host_api == WASAPI:
        return system_default
    return next(
        (device for device in inputs if device.host_api == WASAPI), system_default
    )


def _same_microphone(left: str, right: str) -> bool:
    """Match device names across host APIs, which truncate them differently."""
    a, b = left.strip().lower(), right.strip().lower()
    if not a or not b:
        return False
    return a.startswith(b[:24]) or b.startswith(a[:24])


class CaptureSession:
    """An open microphone. Frames arrive on the audio thread.

    Use as a context manager so the indicator is switched off and the stream
    closed even when the body raises — a capture that outlives its indicator is
    exactly the state FR-013 exists to prevent.
    """

    def __init__(
        self,
        *,
        device_index: int | None = None,
        sample_rate: int = SAMPLE_RATE,
        frame_samples: int = FRAME_SAMPLES,
        on_frame: Callable[[AudioChunk], None] | None = None,
        indicator: Callable[[bool], None] | None = None,
    ) -> None:
        self._device_index = device_index
        self._sample_rate = sample_rate
        self._frame_samples = frame_samples
        self._on_frame = on_frame
        self._indicator = indicator
        self._stream = None
        self._running = threading.Event()
        self._frames_captured = 0

    @property
    def running(self) -> bool:
        return self._running.is_set()

    @property
    def frames_captured(self) -> int:
        return self._frames_captured

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> "CaptureSession":
        sounddevice = _require_sounddevice()
        import numpy  # noqa: PLC0415 - lazy by design

        def callback(indata, _frames, _time, status) -> None:  # pragma: no cover - audio thread
            if status:
                _LOG.debug("capture status: %s", status)
            chunk = AudioChunk(
                samples=numpy.asarray(indata, dtype=numpy.float32).reshape(-1).tobytes(),
                sample_rate=self._sample_rate,
                audio_format=AudioFormat.FLOAT32,
            )
            self._frames_captured += 1
            if self._on_frame is not None:
                try:
                    self._on_frame(chunk)
                except Exception:  # noqa: BLE001 - never kill the audio thread
                    _LOG.exception("a capture consumer raised")

        # WasapiSettings is only valid on a WASAPI device. Passing it to an MME
        # or DirectSound device fails the open outright with
        # "Incompatible host API specific stream info" — which is what happened
        # on every microphone this machine reports by default, so nothing could
        # ever record. Try the right settings for the device, then the other
        # way, rather than assuming either.
        attempts = self._stream_settings(sounddevice)
        last_error: Exception | None = None
        for settings in attempts:
            try:
                self._stream = sounddevice.InputStream(
                    samplerate=self._sample_rate,
                    blocksize=self._frame_samples,
                    device=self._device_index,
                    channels=1,
                    dtype="float32",
                    callback=callback,
                    extra_settings=settings,
                )
                break
            except Exception as exc:  # noqa: BLE001 - try the other host API shape
                last_error = exc
                _LOG.debug(
                    "could not open device %s with %s: %s",
                    self._device_index,
                    "voice-capture processing" if settings is not None else "no extra settings",
                    exc,
                )
        if self._stream is None:
            raise AudioUnavailable(
                f"the microphone could not be opened: {last_error}"
            ) from last_error
        if attempts and attempts[0] is None:
            # Said once, plainly: this device gives no echo cancellation, which
            # is what ADR-0028 leans on to tell our own voice from the user's.
            _LOG.info(
                "device %s is not a WASAPI device, so Windows voice-capture "
                "processing (including echo cancellation) is not available",
                self._device_index,
            )
        # The indicator goes on before the stream does. FR-013 is not satisfied
        # by an indicator that appears a moment after recording begins.
        self._announce(True)
        try:
            self._stream.start()
        except Exception:
            self._announce(False)
            self._stream = None
            raise
        self._running.set()
        return self

    def _stream_settings(self, sounddevice) -> tuple[object | None, ...]:
        """The settings to try, best first, for whichever device was chosen.

        A WASAPI device wants ``WasapiSettings`` and rejects 16 kHz without it;
        every other host API rejects the settings themselves. Getting this
        backwards is not a degradation — the stream simply does not open.
        """
        wasapi = None
        try:
            wasapi = sounddevice.WasapiSettings(auto_convert=True)
        except Exception:  # noqa: BLE001 - not Windows, or no WASAPI
            return (None,)

        if self._is_wasapi_device(sounddevice):
            return (wasapi, None)
        return (None, wasapi)

    def _is_wasapi_device(self, sounddevice) -> bool:
        try:
            index = self._device_index
            if index is None:
                index = sounddevice.default.device[0]
            api_index = int(sounddevice.query_devices(index)["hostapi"])
            return str(sounddevice.query_hostapis(api_index)["name"]) == WASAPI
        except Exception:  # noqa: BLE001 - unknown means try both orders
            _LOG.debug("could not determine the host API for device %s", self._device_index)
            return False

    def stop(self) -> None:
        self._running.clear()
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:  # noqa: BLE001 - closing must not raise onward
                _LOG.exception("could not close the capture stream cleanly")
        self._announce(False)

    def _announce(self, recording: bool) -> None:
        if self._indicator is None:
            return
        try:
            self._indicator(recording)
        except Exception:  # noqa: BLE001 - a broken indicator must not hide it
            _LOG.exception("the recording indicator raised")

    def __enter__(self) -> "CaptureSession":
        return self.start()

    def __exit__(self, *_exc: object) -> None:
        self.stop()


def frames_from_bytes(
    samples: bytes, *, sample_rate: int = SAMPLE_RATE, frame_samples: int = FRAME_SAMPLES
) -> Iterator[AudioChunk]:
    """Cut a recording into frames. Used to replay fixtures through the pipeline."""
    width = 4  # float32
    step = frame_samples * width
    for offset in range(0, len(samples) - step + 1, step):
        yield AudioChunk(
            samples=samples[offset : offset + step],
            sample_rate=sample_rate,
            audio_format=AudioFormat.FLOAT32,
        )
