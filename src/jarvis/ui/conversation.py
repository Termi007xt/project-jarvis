"""The Conversation screen (PRD section 9.5, FR-045, FR-046, FR-047).

Two things this screen must do that a chat window normally does not:

* **Label every reply's source** (FR-047). A model answer and a tool-confirmed
  fact look identical in plain text, and the difference is exactly what the user
  needs in order to know how much to trust it.
* **Make a private session visibly different** (FR-046). "Nothing here is being
  written down" is a promise, and a promise the user cannot see is not one they
  can rely on.

The model call blocks, so it runs on a worker thread. The screen never calls the
engine directly from a slot.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from jarvis.llm.grounding import SourceLabel

__all__ = ["ConversationPanel", "ConversationWorker"]

_LOG = logging.getLogger(__name__)

#: How each source label is shown. Never colour alone — the text carries it too.
_LABEL_STYLE: dict[SourceLabel, tuple[str, str]] = {
    SourceLabel.MODEL_ANSWER: ("#6b7280", "from the local model"),
    SourceLabel.RETRIEVED_FACT: ("#2563eb", "from a retrieved fact"),
    SourceLabel.INFERENCE: ("#b45309", "inferred, not confirmed"),
    SourceLabel.TOOL_RESULT: ("#15803d", "confirmed by a tool"),
    SourceLabel.UNCERTAINTY: ("#b45309", "uncertain"),
}


class ConversationWorker(QObject):
    """Runs one turn off the UI thread. The model call is slow and blocking."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, engine: object, conversation: object, text: str) -> None:
        super().__init__()
        self._engine = engine
        self._conversation = conversation
        self._text = text

    def run(self) -> None:
        try:
            turn = self._engine.ask(self._conversation, self._text)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed
            _LOG.exception("a conversation turn failed")
            self.failed.emit(f"{type(exc).__name__}: {exc}")
            return
        self.finished.emit(turn)


class ConversationPanel(QWidget):
    """Text conversation with the local model."""

    sendRequested = Signal(str)
    privateSessionToggled = Signal(bool)
    historyCleared = Signal()

    def __init__(self, core: object, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._core = core

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QHBoxLayout()
        heading = QLabel("Conversation")
        heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        header.addWidget(heading)
        header.addStretch(1)

        self.private_toggle = QCheckBox("Private session")
        self.private_toggle.setAccessibleName("Private session")
        self.private_toggle.setToolTip(
            "Nothing said in a private session is written to disk — no "
            "conversation record and no memory (PRD FR-046)."
        )
        self.private_toggle.toggled.connect(self.privateSessionToggled.emit)
        header.addWidget(self.private_toggle)

        self.clear_button = QPushButton("Delete history")
        self.clear_button.setAccessibleName("Delete all conversation history")
        self.clear_button.clicked.connect(self.historyCleared.emit)
        header.addWidget(self.clear_button)
        layout.addLayout(header)

        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.status)

        self.transcript = QTextBrowser()
        self.transcript.setAccessibleName("Conversation transcript")
        self.transcript.setOpenExternalLinks(False)
        layout.addWidget(self.transcript, 1)

        entry = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setAccessibleName("Message to Jarvis")
        self.input.setPlaceholderText("Ask Jarvis something…")
        self.input.returnPressed.connect(self._send)
        entry.addWidget(self.input, 1)
        self.send_button = QPushButton("Send")
        self.send_button.setAccessibleName("Send message")
        self.send_button.clicked.connect(self._send)
        entry.addWidget(self.send_button)
        layout.addLayout(entry)

        self._thread: QThread | None = None
        self._worker: ConversationWorker | None = None
        self._busy = False
        self._available = True
        self._reason: str | None = None

    # -- state -------------------------------------------------------------
    def set_availability(self, available: bool, reason: str | None) -> None:
        """Enable or disable input, and say exactly why when disabled.

        The window refreshes every two seconds. While a turn is in flight that
        refresh must not re-enable the input or replace "Thinking…", so the
        availability is remembered and applied once the turn ends.
        """
        self._available = available
        self._reason = reason
        if self._busy:
            return
        self._apply_state()

    def _apply_state(self) -> None:
        self.input.setEnabled(self._available)
        self.send_button.setEnabled(self._available)
        if self._available:
            self.status.setText("Ready. Answers are labelled with where they came from.")
        else:
            self.status.setText(
                self._reason
                or "The local model is not reachable, so Jarvis cannot converse."
            )

    def set_private(self, private: bool) -> None:
        blocked = self.private_toggle.blockSignals(True)
        self.private_toggle.setChecked(private)
        self.private_toggle.blockSignals(blocked)
        if private:
            self.append_note(
                "Private session — nothing from here is written to disk."
            )

    # -- transcript --------------------------------------------------------
    def append_user(self, text: str) -> None:
        self.transcript.append(f"<p><b>You:</b> {_escape(text)}</p>")

    def append_reply(self, text: str, label: SourceLabel) -> None:
        colour, wording = _LABEL_STYLE.get(label, ("#6b7280", label.value))
        self.transcript.append(
            f"<p><b>Jarvis:</b> {_escape(text)}<br>"
            f"<span style='color:{colour};font-size:11px;'>[{wording}]</span></p>"
        )

    def append_note(self, text: str) -> None:
        self.transcript.append(
            f"<p style='color:#6b7280;'><i>{_escape(text)}</i></p>"
        )

    def append_error(self, text: str) -> None:
        self.transcript.append(f"<p style='color:#b91c1c;'><b>Jarvis could not answer:</b> "
                               f"{_escape(text)}</p>")

    def clear_transcript(self) -> None:
        self.transcript.clear()

    # -- sending -----------------------------------------------------------
    def _send(self) -> None:
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self.sendRequested.emit(text)

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        if busy:
            self.input.setEnabled(False)
            self.send_button.setEnabled(False)
            self.status.setText("Thinking…")
        else:
            self._apply_state()

    @property
    def busy(self) -> bool:
        return self._busy

    def transcript_text(self) -> str:
        return self.transcript.toPlainText()


def _escape(text: str) -> str:
    """Everything shown here is data, including the model's own output."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )
