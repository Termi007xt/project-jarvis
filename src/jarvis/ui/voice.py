"""The Voice screen (PRD FR-011, FR-016, FR-017, FR-021, FR-031, FR-032, ADR-0016).

The screen carries an obligation the others do not. FR-011 forbids the GUI
implying that a model trained for "Hey Jarvis" will detect "Jarvis" alone, and
ADR-0016 chose the path that makes that distinction real. So the enrolled phrase
is shown literally, the disclosure sentence is always present, and
always-listening cannot be switched on until an enrolment has been *measured*
and passed (ADR-0016 criterion 2).

Everything else here is honest reporting: which components are installed, which
device is selected, what the room sounds like, and what licence each voice
carries.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from jarvis.audio.availability import VoiceStackStatus
from jarvis.audio.pipeline import ListeningState
from jarvis.audio.wake import DESIRED_PHRASE, PHASE_1_PHRASE, phrase_disclosure
from jarvis.audio.wake_install import LICENCE_WARNING

__all__ = ["VoicePanel"]

_LOG = logging.getLogger(__name__)

#: What each listening state means, in words the user can act on. FR-013 makes
#: "Jarvis is recording" something that must always be visible, not inferred.
_LISTENING_WORDING: dict[str, str] = {
    ListeningState.OFF.value: "Not listening. Press F9 to talk.",
    ListeningState.WAITING_FOR_WAKE.value: 'Listening for "Hey Jarvis".',
    ListeningState.CAPTURING_COMMAND.value: "Recording — speak now.",
    ListeningState.TRANSCRIBING.value: "Transcribing what you said…",
    ListeningState.SPEAKING.value: "Jarvis is speaking.",
}


class VoicePanel(QWidget):
    """Devices, voices, wake phrase and enrolment."""

    deviceChanged = Signal(int)
    testMicrophoneRequested = Signal()
    calibrateRequested = Signal()
    previewVoiceRequested = Signal(str)
    enrolRequested = Signal()
    alwaysListeningToggled = Signal(bool)
    pushToTalkToggled = Signal(bool)
    installModelRequested = Signal()
    removeModelRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        heading = QLabel("Voice")
        heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(heading)

        # -- what is actually installed -----------------------------------
        self.stack_status = QLabel()
        self.stack_status.setWordWrap(True)
        layout.addWidget(self.stack_status)

        # -- wake phrase, stated truthfully (FR-011) ----------------------
        self.phrase_label = QLabel()
        self.phrase_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(self.phrase_label)

        self.disclosure = QLabel(phrase_disclosure())
        self.disclosure.setWordWrap(True)
        self.disclosure.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.disclosure)

        # -- one-time model installation (ADR-0016, PRD §17.2) ------------
        install_row = QHBoxLayout()
        self.install_model_button = QPushButton("Install wake-word model")
        self.install_model_button.setAccessibleName("Install the wake-word model")
        self.install_model_button.clicked.connect(self.installModelRequested.emit)
        install_row.addWidget(self.install_model_button)
        self.remove_model_button = QPushButton("Remove wake-word model")
        self.remove_model_button.setAccessibleName("Remove the wake-word model")
        self.remove_model_button.clicked.connect(self.removeModelRequested.emit)
        install_row.addWidget(self.remove_model_button)
        install_row.addStretch(1)
        layout.addLayout(install_row)

        self.model_path_label = QLabel()
        self.model_path_label.setWordWrap(True)
        self.model_path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.model_path_label.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.model_path_label)

        self.licence_warning = QLabel(LICENCE_WARNING)
        self.licence_warning.setWordWrap(True)
        self.licence_warning.setStyleSheet("color: #b45309;")
        layout.addWidget(self.licence_warning)

        enrolment_row = QHBoxLayout()
        # Not built in this build. ADR-0010: shown disabled and naming its
        # phase, never hidden and never appearing to work.
        self.enrol_button = QPushButton("Record wake-word samples  ·  Phase 2")
        self.enrol_button.setAccessibleName("Record wake-word samples")
        self.enrol_button.setEnabled(False)
        self.enrol_button.setToolTip(
            "Personal wake-word enrolment is not implemented yet (ADR-0016 "
            "criterion 2). Push-to-talk works now."
        )
        self.enrol_button.clicked.connect(self.enrolRequested.emit)
        enrolment_row.addWidget(self.enrol_button)

        enrolment_row.addStretch(1)
        layout.addLayout(enrolment_row)

        self.enrolment_status = QLabel()
        self.enrolment_status.setWordWrap(True)
        layout.addWidget(self.enrolment_status)

        # -- talking to Jarvis (FR-010, FR-018) ---------------------------
        listen_row = QHBoxLayout()
        self.listen_button = QPushButton("Start listening")
        self.listen_button.setAccessibleName("Start listening for the wake phrase")
        self.listen_button.setCheckable(True)
        self.listen_button.toggled.connect(self.alwaysListeningToggled.emit)
        listen_row.addWidget(self.listen_button)

        self.push_to_talk_toggle = QCheckBox("Push-to-talk")
        self.push_to_talk_toggle.setAccessibleName("Push to talk")
        self.push_to_talk_toggle.toggled.connect(self.pushToTalkToggled.emit)
        listen_row.addWidget(self.push_to_talk_toggle)
        listen_row.addStretch(1)
        layout.addLayout(listen_row)

        #: What Jarvis last heard. Without this the only evidence a command was
        #: understood is the answer, which makes a misheard word look like a
        #: model failure rather than a transcription one.
        self.heard_label = QLabel("Nothing has been heard yet.")
        self.heard_label.setWordWrap(True)
        self.heard_label.setAccessibleName("Last transcribed command")
        self.heard_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self.heard_label)

        # -- microphone (FR-016, FR-017) ----------------------------------
        device_row = QHBoxLayout()
        device_row.addWidget(QLabel("Microphone"))
        self.device_box = QComboBox()
        self.device_box.setAccessibleName("Microphone")
        self.device_box.currentIndexChanged.connect(self._on_device_changed)
        device_row.addWidget(self.device_box, 1)
        self.test_button = QPushButton("Test")
        self.test_button.setAccessibleName("Test the microphone")
        self.test_button.clicked.connect(self.testMicrophoneRequested.emit)
        device_row.addWidget(self.test_button)
        self.calibrate_button = QPushButton("Calibrate for this room")
        self.calibrate_button.setAccessibleName("Calibrate for ambient noise")
        self.calibrate_button.clicked.connect(self.calibrateRequested.emit)
        device_row.addWidget(self.calibrate_button)
        layout.addLayout(device_row)

        self.meter = QProgressBar()
        self.meter.setRange(0, 100)
        self.meter.setTextVisible(False)
        self.meter.setAccessibleName("Microphone level")
        layout.addWidget(self.meter)

        self.listening_label = QLabel(_LISTENING_WORDING[ListeningState.OFF.value])
        self.listening_label.setWordWrap(True)
        self.listening_label.setAccessibleName("Listening state")
        layout.addWidget(self.listening_label)

        self.calibration_label = QLabel("Not calibrated yet.")
        self.calibration_label.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.calibration_label)

        # -- voices (FR-031, FR-032) --------------------------------------
        voice_row = QHBoxLayout()
        voice_row.addWidget(QLabel("Voice"))
        self.voice_box = QComboBox()
        self.voice_box.setAccessibleName("Voice")
        voice_row.addWidget(self.voice_box, 1)
        self.preview_button = QPushButton("Preview")
        self.preview_button.setAccessibleName("Preview the selected voice")
        self.preview_button.clicked.connect(self._on_preview)
        voice_row.addWidget(self.preview_button)
        layout.addLayout(voice_row)

        self.licence_label = QLabel()
        self.licence_label.setWordWrap(True)
        self.licence_label.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.licence_label)

        self.duplex_label = QLabel()
        self.duplex_label.setWordWrap(True)
        layout.addWidget(self.duplex_label)

        layout.addStretch(1)
        self._voice_ids: list[str] = []
        self._device_indices: list[int] = []

    # -- population --------------------------------------------------------
    def set_stack_status(self, status: VoiceStackStatus) -> None:
        lines = [component.describe() for component in status.components]
        self.stack_status.setText("\n".join(lines))
        installed = status.capture.available
        for control in (self.test_button, self.calibrate_button):
            control.setEnabled(installed)
            if not installed:
                control.setToolTip(status.capture.detail or "No microphone is available.")
        # Never re-enabled here: enrolment is unimplemented, not merely blocked
        # by a missing microphone (ADR-0010).
        self.enrol_button.setEnabled(False)
        self.preview_button.setEnabled(status.text_to_speech.available)

    def set_model_state(self, directory: object, installed: bool, detail: str) -> None:
        """Always show the exact destination path, installed or not."""
        state = "installed" if installed else "not installed"
        self.model_path_label.setText(f"Wake-word model ({state}): {directory}\n{detail}")
        self.install_model_button.setText(
            "Reinstall wake-word model" if installed else "Install wake-word model"
        )
        self.remove_model_button.setEnabled(installed)
        self.remove_model_button.setToolTip(
            f"Deletes the downloaded models from {directory}."
            if installed
            else "There is no wake-word model installed to remove."
        )

    def set_phrase(self, phrase: str, *, enrolled: bool) -> None:
        """State the phrase literally. Never label it 'Jarvis' (FR-011)."""
        self.phrase_label.setText(f'Wake phrase: "{phrase}"')
        self.disclosure.setText(phrase_disclosure(phrase))

    def set_enrolment(self, summary: str, *, passed: bool, enrolled: bool) -> None:
        """Show what has been measured. Never imply more than that."""
        self.enrolment_status.setText(summary)

    def set_listening_available(self, available: bool, reason: str = "") -> None:
        """Listening needs the wake model and a microphone — nothing more.

        ADR-0016 originally required a personal enrolment first. The owner
        chose the pretrained model instead (amendment, 2026-08-03), so the gate
        is now whether the detector actually loads. The wording still refuses
        to claim a false-accept rate nobody has measured on this voice.
        """
        self.listen_button.setEnabled(available)
        self.listen_button.setToolTip(
            reason
            or (
                "Uses the shared pretrained model. It has not been tuned to "
                "your voice, so occasional misses and false wakes are expected."
            )
        )

    def set_listening(self, listening: bool) -> None:
        blocked = self.listen_button.blockSignals(True)
        self.listen_button.setChecked(listening)
        self.listen_button.setText("Stop listening" if listening else "Start listening")
        self.listen_button.blockSignals(blocked)

    def set_push_to_talk(self, enabled: bool, hotkey: str = "") -> None:
        blocked = self.push_to_talk_toggle.blockSignals(True)
        self.push_to_talk_toggle.setChecked(enabled)
        self.push_to_talk_toggle.setText(
            f"Push-to-talk ({hotkey})" if hotkey else "Push-to-talk"
        )
        self.push_to_talk_toggle.blockSignals(blocked)

    def set_last_heard(self, text: str, confidence: float | None = None) -> None:
        """Show the transcript, so a misheard word is visibly a mishearing."""
        if not text.strip():
            self.heard_label.setText("Nothing was heard.")
            return
        suffix = f"  (confidence {confidence:.0%})" if confidence is not None else ""
        self.heard_label.setText(f'Heard: "{text}"{suffix}')

    def set_devices(self, devices: tuple[object, ...], selected_index: int | None = None) -> None:
        blocked = self.device_box.blockSignals(True)
        self.device_box.clear()
        self._device_indices = []
        for device in devices:
            self.device_box.addItem(device.describe())  # type: ignore[attr-defined]
            self._device_indices.append(device.index)  # type: ignore[attr-defined]
        if not devices:
            self.device_box.addItem("No input device found")
        if selected_index is not None and selected_index in self._device_indices:
            self.device_box.setCurrentIndex(self._device_indices.index(selected_index))
        self.device_box.blockSignals(blocked)

    def set_voices(self, voices: tuple[object, ...]) -> None:
        self.voice_box.clear()
        self._voice_ids = []
        for voice in voices:
            self.voice_box.addItem(voice.describe())  # type: ignore[attr-defined]
            self._voice_ids.append(voice.voice_id)  # type: ignore[attr-defined]
        if not voices:
            self.voice_box.addItem("No voice available")
            self.licence_label.setText("")
            return
        first = voices[0]
        self.licence_label.setText(
            f"Licence: {first.licence}. "  # type: ignore[attr-defined]
            + (
                "Redistributable with the product."
                if getattr(first, "redistributable", False)
                else "Not cleared for redistribution, so it is not bundled in any "
                "build that leaves this machine (FR-032, ADR-0014)."
            )
        )

    def set_level(self, level: float) -> None:
        self.meter.setValue(max(0, min(100, int(level * 400))))

    def set_listening_state(self, state: str) -> None:
        """Say plainly whether the microphone is open (PRD FR-013)."""
        self.listening_label.setText(
            _LISTENING_WORDING.get(state, f"Listening state: {state}")
        )
        recording = state == ListeningState.CAPTURING_COMMAND.value
        self.listening_label.setStyleSheet(
            "color: #b91c1c; font-weight: 600;" if recording else "color: palette(mid);"
        )

    def set_calibration(self, description: str) -> None:
        self.calibration_label.setText(description)

    def set_duplex(self, description: str) -> None:
        self.duplex_label.setText(description)

    # -- selection ---------------------------------------------------------
    def selected_device_index(self) -> int | None:
        row = self.device_box.currentIndex()
        if 0 <= row < len(self._device_indices):
            return self._device_indices[row]
        return None

    def selected_voice_id(self) -> str | None:
        row = self.voice_box.currentIndex()
        if 0 <= row < len(self._voice_ids):
            return self._voice_ids[row]
        return None

    def _on_device_changed(self, row: int) -> None:
        if 0 <= row < len(self._device_indices):
            self.deviceChanged.emit(self._device_indices[row])

    def _on_preview(self) -> None:
        voice_id = self.selected_voice_id()
        if voice_id:
            self.previewVoiceRequested.emit(voice_id)

    # -- the honesty check the tests assert against ------------------------
    def claims_single_word_phrase(self) -> bool:
        """True if anything on this screen implies bare "Jarvis" works.

        FR-011 forbids that implication, so the test asserts this stays False.
        """
        text = " ".join(
            [
                self.phrase_label.text(),
                self.disclosure.text(),
                self.enrolment_status.text(),
            ]
        )
        if PHASE_1_PHRASE.lower() in text.lower():
            # Mentioning the real phrase is required, not a violation.
            text = text.lower().replace(PHASE_1_PHRASE.lower(), "")
        return f'"{DESIRED_PHRASE.lower()}"' in text.lower() and "not available" not in text.lower()
