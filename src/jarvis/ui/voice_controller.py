"""Joins the voice service to the shell (PRD FR-013, FR-016, FR-017, FR-018).

The service, the pipeline and every provider were built and reported honestly
on the Voice screen — but nothing was connected to them. Push-to-talk said the
stack "is not available on this machine yet" while it was fully installed, a
finished spoken command had no listener, the level meter had no source, and the
Test, Calibrate and Preview buttons were enabled and wired to nothing.

Two rules shape this module:

* **Audio callbacks arrive on the audio thread.** Nothing here touches a widget
  from one. Every callback emits a Qt signal, which is delivered on the GUI
  thread by queued connection; the slots are the only code that touches Qt.
* **Blocking work never runs on the GUI thread.** Transcription loads a model
  and synthesis renders audio, both of which take seconds. They run on plain
  daemon threads that are joined, with a bound, at shutdown.

What is *not* wired is as deliberate as what is: there is no wake-word enrolment
implementation in this build, so its button is disabled and says why rather than
appearing to work (ADR-0010, ADR-0016).
"""

from __future__ import annotations

import logging
import threading
from typing import Callable

from PySide6.QtCore import QObject, Qt, Signal

from jarvis.audio.pipeline import CommandHeard, ListeningState

__all__ = ["VoiceController"]

_LOG = logging.getLogger(__name__)

#: How long the microphone test runs before closing itself. Long enough to see
#: the meter move, short enough that a forgotten test does not hold the mic.
TEST_SECONDS = 5.0

#: Ambient noise is measured over this window (PRD FR-017).
CALIBRATION_SECONDS = 3.0

PREVIEW_TEXT = "This is the voice Jarvis will use when it speaks to you."


class VoiceController(QObject):
    """Owns everything that connects the Voice screen and F9 to the service."""

    #: A finished spoken command, already on the GUI thread.
    commandHeard = Signal(str)
    levelChanged = Signal(float)
    listeningStateChanged = Signal(str)
    noticed = Signal(str, str)  # title, message — shown as a tray notification
    calibrated = Signal(str)
    busyChanged = Signal(bool)

    def __init__(self, voice: object, panel: object, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._voice = voice
        self._panel = panel
        self._threads: list[threading.Thread] = []
        self._test_timer: threading.Timer | None = None
        self._closing = threading.Event()

        # Queued: these are emitted from the audio thread.
        self.levelChanged.connect(self._on_level, Qt.ConnectionType.QueuedConnection)
        self.listeningStateChanged.connect(
            self._on_state, Qt.ConnectionType.QueuedConnection
        )

        voice.set_command_listener(self._command_from_audio_thread)  # type: ignore[attr-defined]
        voice.set_state_listener(self._state_from_audio_thread)  # type: ignore[attr-defined]
        voice.set_level_listener(self._level_from_audio_thread)  # type: ignore[attr-defined]

        self._connect_panel()

    # -- panel wiring ------------------------------------------------------
    def _connect_panel(self) -> None:
        panel = self._panel
        panel.deviceChanged.connect(self.set_input_device)  # type: ignore[attr-defined]
        panel.testMicrophoneRequested.connect(self.test_microphone)  # type: ignore[attr-defined]
        panel.calibrateRequested.connect(self.calibrate)  # type: ignore[attr-defined]
        panel.previewVoiceRequested.connect(self.preview_voice)  # type: ignore[attr-defined]
        panel.enrolRequested.connect(self._enrolment_not_built)  # type: ignore[attr-defined]

    # -- callbacks from the audio thread -----------------------------------
    def _command_from_audio_thread(self, command: CommandHeard) -> None:
        if command is None or command.empty:
            return
        _LOG.info("heard a command by %s", command.route.value)
        self.commandHeard.emit(command.text)

    def _state_from_audio_thread(self, state: ListeningState) -> None:
        self.listeningStateChanged.emit(state.value)

    def _level_from_audio_thread(self, level: float) -> None:
        self.levelChanged.emit(level)

    # -- slots on the GUI thread -------------------------------------------
    def _on_level(self, level: float) -> None:
        self._panel.set_level(level)  # type: ignore[attr-defined]

    def _on_state(self, state: str) -> None:
        self._panel.set_listening_state(state)  # type: ignore[attr-defined]

    # -- push to talk (FR-018) ---------------------------------------------
    def toggle_push_to_talk(self) -> None:
        """F9. Press to start, and again to cut it short.

        ``RegisterHotKey`` reports the press only — there is no key-up — so this
        cannot be a hold-to-talk. Speech normally ends by itself when the voice
        activity detector hears silence.
        """
        voice = self._voice
        if voice.capturing_command:  # type: ignore[attr-defined]
            self._run_off_thread("end-push-to-talk", self._end_push_to_talk)
            return

        if not voice.capture_available:  # type: ignore[attr-defined]
            self.noticed.emit(
                "Push to talk is not available",
                "The microphone cannot be opened. The Voice screen says what is missing.",
            )
            return
        if not voice.begin_push_to_talk():  # type: ignore[attr-defined]
            self.noticed.emit(
                "Push to talk could not start",
                "The microphone could not be opened. See the Voice screen.",
            )
            return
        self.noticed.emit("Listening", "Speak now. Press F9 again to stop early.")

    def _end_push_to_talk(self) -> None:
        """Transcription blocks for seconds, so never on the GUI thread."""
        command = self._voice.end_push_to_talk()  # type: ignore[attr-defined]
        if command is None or command.empty:
            self.noticed.emit("Nothing was heard", "No speech was transcribed.")
            return
        self.commandHeard.emit(command.text)

    # -- device selection (FR-016) -----------------------------------------
    def set_input_device(self, device_index: int) -> None:
        """Switch microphone. Reopens the stream if one is already open."""
        if not self._voice.set_input_device(device_index):  # type: ignore[attr-defined]
            self.noticed.emit(
                "That microphone did not open",
                "The previously selected device was closed. Choose another.",
            )
            return
        _LOG.info("input device set to %s", device_index)

    # -- microphone test (FR-016) ------------------------------------------
    def test_microphone(self) -> None:
        voice = self._voice
        if not voice.capture_available:  # type: ignore[attr-defined]
            self.noticed.emit(
                "No microphone", "Audio capture is not available on this machine."
            )
            return
        if voice.capturing:  # type: ignore[attr-defined]
            self.noticed.emit("Already listening", "The microphone is already open.")
            return
        if not voice.start_capture():  # type: ignore[attr-defined]
            self.noticed.emit("The microphone did not open", "See the Voice screen.")
            return

        self.noticed.emit(
            "Microphone test", f"Speak — the meter moves for {TEST_SECONDS:.0f} seconds."
        )
        self._test_timer = threading.Timer(TEST_SECONDS, self._end_test)
        self._test_timer.daemon = True
        self._test_timer.start()

    def _end_test(self) -> None:
        try:
            self._voice.stop_capture()  # type: ignore[attr-defined]
        finally:
            self.levelChanged.emit(0.0)
            self.noticed.emit("Microphone test finished", "The microphone is closed again.")

    # -- calibration (FR-017) ----------------------------------------------
    def calibrate(self) -> None:
        if not self._voice.capture_available:  # type: ignore[attr-defined]
            self.noticed.emit(
                "No microphone", "Ambient noise cannot be measured without one."
            )
            return
        self._run_off_thread("calibrate", self._calibrate)

    def _calibrate(self) -> None:
        """Collect a few seconds of room tone, then set the threshold."""
        voice = self._voice
        frames: list[object] = []
        collecting = threading.Event()
        collecting.set()

        def collect(level_frame) -> None:
            if collecting.is_set():
                frames.append(level_frame)

        started_here = not voice.capturing  # type: ignore[attr-defined]
        if started_here and not voice.start_capture():  # type: ignore[attr-defined]
            self.noticed.emit("Calibration failed", "The microphone could not be opened.")
            return

        self.noticed.emit(
            "Measuring the room",
            f"Stay quiet for {CALIBRATION_SECONDS:.0f} seconds.",
        )
        # Frames arrive through the pipeline; tap them for the duration.
        voice.pipeline.add_frame_observer(collect)  # type: ignore[attr-defined]
        try:
            self._closing.wait(CALIBRATION_SECONDS)
        finally:
            collecting.clear()
            voice.pipeline.remove_frame_observer(collect)  # type: ignore[attr-defined]
            if started_here:
                voice.stop_capture()  # type: ignore[attr-defined]

        if not frames:
            self.noticed.emit(
                "Calibration failed", "No audio arrived from the microphone."
            )
            return
        calibration = voice.calibrate_from(frames)  # type: ignore[attr-defined]
        self.calibrated.emit(calibration.describe())
        self.noticed.emit("Room measured", calibration.describe())

    # -- voice preview (FR-031, FR-032) ------------------------------------
    def preview_voice(self, voice_id: str) -> None:
        self._run_off_thread("preview", lambda: self._preview(voice_id))

    def _preview(self, voice_id: str) -> None:
        self.busyChanged.emit(True)
        try:
            result = self._voice.speak(PREVIEW_TEXT, voice_id=voice_id)  # type: ignore[attr-defined]
        finally:
            self.busyChanged.emit(False)
        if result is None:
            self.noticed.emit(
                "No voice", "Nothing could be synthesised. See the Voice screen."
            )
            return
        if not result.spoken_aloud:
            # Never report a preview as played when it was not (FR-048).
            self.noticed.emit(
                "Nothing was heard",
                result.playback.error or "the audio never reached the output device",
            )
            return
        self.noticed.emit("Preview", result.playback.describe())

    # -- what is deliberately not built ------------------------------------
    def _enrolment_not_built(self) -> None:
        """ADR-0010: name the phase rather than pretending or failing quietly."""
        self.noticed.emit(
            "Wake-word enrolment is not built yet",
            "Recording personal wake-word samples is planned but not implemented. "
            "Push-to-talk works now, and the pretrained 'Hey Jarvis' model is "
            "installed.",
        )

    # -- lifecycle ---------------------------------------------------------
    def _run_off_thread(self, name: str, work: Callable[[], None]) -> None:
        def guarded() -> None:
            try:
                work()
            except Exception:  # noqa: BLE001 - a voice action must not kill the app
                _LOG.exception("the voice action '%s' failed", name)
                self.noticed.emit("That did not work", f"The {name} action failed.")

        thread = threading.Thread(target=guarded, name=f"jarvis-voice-{name}", daemon=True)
        self._threads.append(thread)
        thread.start()

    def shutdown(self, timeout_seconds: float = 3.0) -> None:
        """Stop listening and let the workers finish, with a bound."""
        self._closing.set()
        if self._test_timer is not None:
            self._test_timer.cancel()
        try:
            self._voice.stop_capture()  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            _LOG.exception("could not close the microphone")
        for thread in list(self._threads):
            thread.join(timeout=timeout_seconds)
            if thread.is_alive():
                _LOG.warning("voice worker %s did not stop in time", thread.name)
        self._threads.clear()
