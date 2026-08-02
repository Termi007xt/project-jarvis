"""Tray state icons, drawn programmatically.

Two reasons not to ship image files: PRD section 17.3 forbids redistributing
assets without clearance and no original icon set exists yet, and PRD NFR-033
forbids relying on colour alone. Each state therefore gets a distinct *shape* as
well as a distinct colour, plus a tooltip and an accessible name supplied by the
tray.
"""

from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF

__all__ = ["TrayState", "tray_icon", "state_colour"]


class TrayState(str, Enum):
    """PRD section 9.1 tray states."""

    OFFLINE = "offline"
    IDLE = "idle"
    RECORDING = "recording"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    BLOCKED = "blocked"

    @property
    def label(self) -> str:
        # PRD section 9.1 describes the blue state as "idle and listening for
        # wake phrase". The label says only "Idle", because nothing is
        # listening until the audio subsystem exists in Phase 1, and a tooltip
        # that claims otherwise would be exactly the kind of unsupported status
        # message PRD section 1.10 forbids. The audio worker supplies the
        # "listening" detail when listening is genuinely active.
        return {
            TrayState.OFFLINE: "Offline or disabled",
            TrayState.IDLE: "Idle",
            TrayState.RECORDING: "Recording a command",
            TrayState.THINKING: "Thinking or planning",
            TrayState.ACTING: "Performing an action",
            TrayState.WAITING: "Waiting or paused",
            TrayState.BLOCKED: "Blocked, error, or approval required",
        }[self]

    @property
    def shape(self) -> str:
        """A non-colour distinguishing mark (PRD NFR-033)."""
        return {
            TrayState.OFFLINE: "hollow circle",
            TrayState.IDLE: "filled circle",
            TrayState.RECORDING: "filled circle with ring",
            TrayState.THINKING: "three dots",
            TrayState.ACTING: "arrow",
            TrayState.WAITING: "pause bars",
            TrayState.BLOCKED: "cross",
        }[self]


_COLOURS: dict[TrayState, str] = {
    TrayState.OFFLINE: "#8b949e",
    TrayState.IDLE: "#2f81f7",
    TrayState.RECORDING: "#2ea043",
    TrayState.THINKING: "#a371f7",
    TrayState.ACTING: "#e3873c",
    TrayState.WAITING: "#d4a72c",
    TrayState.BLOCKED: "#d1242f",
}


def state_colour(state: TrayState) -> QColor:
    return QColor(_COLOURS[state])


def tray_icon(state: TrayState, size: int = 64) -> QIcon:
    """Render the icon for a state. Colour *and* shape differ per state."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    colour = state_colour(state)
    margin = size * 0.12
    body = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)

    if state is TrayState.OFFLINE:
        painter.setPen(QPen(colour, size * 0.09))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(body)
    else:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(colour))
        painter.drawEllipse(body)

    painter.setPen(QPen(QColor("#ffffff"), size * 0.08, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    centre = QPointF(size / 2, size / 2)
    unit = size / 2

    if state is TrayState.RECORDING:
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(centre, unit * 0.36, unit * 0.36)
    elif state is TrayState.THINKING:
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(Qt.PenStyle.NoPen)
        for offset in (-0.38, 0.0, 0.38):
            painter.drawEllipse(
                QPointF(centre.x() + unit * offset, centre.y()), unit * 0.1, unit * 0.1
            )
    elif state is TrayState.ACTING:
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(Qt.PenStyle.NoPen)
        arrow = QPolygonF(
            [
                QPointF(centre.x() - unit * 0.28, centre.y() - unit * 0.36),
                QPointF(centre.x() + unit * 0.40, centre.y()),
                QPointF(centre.x() - unit * 0.28, centre.y() + unit * 0.36),
            ]
        )
        painter.drawPolygon(arrow)
    elif state is TrayState.WAITING:
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(Qt.PenStyle.NoPen)
        bar_width = unit * 0.16
        bar_height = unit * 0.66
        painter.drawRect(
            QRectF(centre.x() - unit * 0.32, centre.y() - bar_height / 2, bar_width, bar_height)
        )
        painter.drawRect(
            QRectF(centre.x() + unit * 0.16, centre.y() - bar_height / 2, bar_width, bar_height)
        )
    elif state is TrayState.BLOCKED:
        reach = unit * 0.33
        painter.drawLine(
            QPointF(centre.x() - reach, centre.y() - reach),
            QPointF(centre.x() + reach, centre.y() + reach),
        )
        painter.drawLine(
            QPointF(centre.x() + reach, centre.y() - reach),
            QPointF(centre.x() - reach, centre.y() + reach),
        )

    painter.end()
    return QIcon(pixmap)
