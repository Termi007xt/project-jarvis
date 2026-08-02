"""The approval surface (PRD section 11.2, ADR-0027).

Tray-anchored and **non-modal**, which is the whole point: a modal dialog takes
keyboard focus, and from Phase 2 onwards Jarvis is often driving another
application when it needs to ask something. Stealing focus mid-action can break
the automation the user is being asked to approve, and can send the next
keystroke to the wrong window.

Non-modal means visibility has to be engineered rather than assumed, so three
things carry it instead: the tray turns red while a request is pending, the
request is listed in the window with working controls, and it times out rather
than waiting forever. All three are required; none of them is decorative.

This module renders and collects. Every decision it gathers goes back through
:class:`~jarvis.core.tools.approvals.ApprovalQueue`, which is where the rules
about what may be offered actually live.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from jarvis.core.permissions.models import Decision, GrantScope, RiskLevel
from jarvis.core.tools.approvals import ApprovalQueue, PendingApproval
from jarvis.core.tools.ports import RememberDenialOption

__all__ = ["ApprovalPanel", "ApprovalController", "scope_button_label"]

_LOG = logging.getLogger(__name__)

#: Wording for each offerable scope. PRD section 11.2 names the first three;
#: "Allow always" is ADR-0027's low-risk option.
_SCOPE_LABELS: dict[GrantScope, str] = {
    GrantScope.ONCE: "Allow once",
    GrantScope.TASK: "Allow for this task",
    GrantScope.ALWAYS: "Allow always",
    GrantScope.SESSION: "Allow for this session",
}

_RISK_TEXT: dict[RiskLevel, str] = {
    RiskLevel.LOW: "Low risk",
    RiskLevel.MEDIUM: "Medium risk",
    RiskLevel.HIGH: "High risk — confirmation is required every time",
    RiskLevel.PROHIBITED: "Prohibited",
}


def scope_button_label(scope: GrantScope) -> str:
    return _SCOPE_LABELS.get(scope, f"Allow ({scope.value})")


class ApprovalPanel(QWidget):
    """One pending request, rendered with the PRD section 11.2 field set."""

    answered = Signal(str, object, object, object)  # approval_id, decision, scope, denial
    stopTaskRequested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        # The load-bearing attribute: show without taking focus from whatever
        # the user (or Jarvis) is doing.
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setObjectName("approvalPanel")
        self.setAccessibleName("Jarvis approval request")
        self.setFixedWidth(460)

        self._approval_id: str | None = None
        self._buttons: list[QWidget] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("approvalCard")
        card.setFrameShape(QFrame.Shape.StyledPanel)
        outer.addWidget(card)

        self._layout = QVBoxLayout(card)
        self._layout.setContentsMargins(18, 18, 18, 18)
        self._layout.setSpacing(8)

        self.heading = QLabel()
        self.heading.setStyleSheet("font-size: 15px; font-weight: 600;")
        self.heading.setWordWrap(True)
        self._layout.addWidget(self.heading)

        self.risk_label = QLabel()
        self.risk_label.setWordWrap(True)
        self._layout.addWidget(self.risk_label)

        self.detail = QLabel()
        self.detail.setWordWrap(True)
        self.detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._layout.addWidget(self.detail)

        self.countdown = QLabel()
        self.countdown.setStyleSheet("color: palette(mid);")
        self._layout.addWidget(self.countdown)

        self.button_row = QVBoxLayout()
        self.button_row.setSpacing(6)
        self._layout.addLayout(self.button_row)

        self._ticker = QTimer(self)
        self._ticker.setInterval(1000)
        self._ticker.timeout.connect(self._tick)

    # -- rendering ---------------------------------------------------------
    def show_request(self, pending: PendingApproval) -> None:
        request = pending.request
        self._approval_id = request.approval_id
        self._pending = pending

        self.heading.setText(request.action_summary)
        self.risk_label.setText(
            f"{_RISK_TEXT.get(request.risk, request.risk.value)}"
            f"  ·  {'reversible' if request.reversible else 'not reversible'}"
        )
        self.detail.setText(self._describe(pending))
        self._rebuild_buttons(pending)
        self._tick()
        self._ticker.start()

        self._anchor()
        self.show()
        self.raise_()

    @staticmethod
    def _describe(pending: PendingApproval) -> str:
        """Every PRD section 11.2 field, and no field invented to fill a gap."""
        request = pending.request
        lines = [
            f"<b>Capability</b> {request.capability_title or request.capability_id}",
            f"<b>Tool</b> {request.tool_id}",
        ]
        if request.initiating_utterance:
            lines.append(f"<b>You asked</b> {request.initiating_utterance}")
        if request.target:
            lines.append(f"<b>Target</b> {request.target}")
        if request.parameters:
            shown = ", ".join(f"{k}={v}" for k, v in sorted(request.parameters.items()))
            lines.append(f"<b>Data involved</b> {shown}")
        elif request.data_involved:
            lines.append(f"<b>Data involved</b> {request.data_involved}")
        lines.append(f"<b>Scope</b> {request.scope_description}")
        if not request.reversible:
            lines.append("<b>This cannot be undone.</b>")
        elif request.rollback_method:
            lines.append(f"<b>Reversible by</b> {request.rollback_method}")
        return "<br>".join(lines)

    def _rebuild_buttons(self, pending: PendingApproval) -> None:
        for widget in self._buttons:
            self.button_row.removeWidget(widget)
            # Reparenting first is what actually detaches it. ``deleteLater``
            # alone defers to the event loop, and until that runs the old
            # buttons are still children — which would mean a request showing
            # controls belonging to the previous one.
            widget.setParent(None)
            widget.deleteLater()
        self._buttons.clear()

        request = pending.request
        allow_container = QWidget()
        allow_row = QHBoxLayout(allow_container)
        allow_row.setContentsMargins(0, 0, 0, 0)
        for scope in request.offerable_scopes:
            button = QPushButton(scope_button_label(scope), allow_container)
            button.setAccessibleName(f"{scope_button_label(scope)} — {request.action_summary}")
            button.clicked.connect(
                lambda _checked=False, s=scope: self._answer(Decision.ALLOW, s, None)
            )
            allow_row.addWidget(button)
        self._add_button_widget(allow_container)

        deny = QPushButton("Deny")
        deny.setAccessibleName(f"Deny — {request.action_summary}")
        deny.setDefault(True)
        deny.clicked.connect(lambda: self._answer(Decision.DENY, GrantScope.ONCE, None))
        self._add_button_widget(deny)

        for option in request.denial_options:
            remember = QPushButton(option.label)
            remember.setAccessibleName(f"{option.label} — {request.action_summary}")
            remember.clicked.connect(
                lambda _checked=False, o=option: self._answer(Decision.DENY, GrantScope.ONCE, o)
            )
            self._add_button_widget(remember)

        if request.task_id:
            stop = QPushButton("Deny and stop the task")
            stop.setAccessibleName(f"Deny and stop the task — {request.action_summary}")
            stop.clicked.connect(self._stop_task)
            self._add_button_widget(stop)

    def _add_button_widget(self, widget: QWidget) -> None:
        self.button_row.addWidget(widget)
        self._buttons.append(widget)

    def _anchor(self) -> None:
        """Bottom-right of the available desktop — where the tray lives."""
        screen = self.screen()
        if screen is None:  # pragma: no cover - always set once shown
            return
        area = screen.availableGeometry()
        self.adjustSize()
        self.move(
            area.right() - self.width() - 16,
            area.bottom() - self.sizeHint().height() - 16,
        )

    # -- answering ---------------------------------------------------------
    def _answer(
        self, decision: Decision, scope: GrantScope, denial: RememberDenialOption | None
    ) -> None:
        if self._approval_id is None:
            return
        approval_id, self._approval_id = self._approval_id, None
        self._ticker.stop()
        self.hide()
        self.answered.emit(approval_id, decision, scope, denial)

    def _stop_task(self) -> None:
        if self._approval_id is None:
            return
        approval_id = self._approval_id
        self.stopTaskRequested.emit(approval_id)
        self._answer(Decision.DENY, GrantScope.ONCE, None)

    def _tick(self) -> None:
        pending = getattr(self, "_pending", None)
        if pending is None:
            return
        remaining = int(pending.seconds_remaining())
        # Saying what silence means is the honest part: the user should never
        # discover the timeout behaviour by being surprised at the outcome.
        self.countdown.setText(
            f"Expires in {remaining}s. If you do not answer, this is denied."
        )
        if remaining <= 0:
            self._ticker.stop()
            self._approval_id = None
            self.hide()

    @property
    def current_approval_id(self) -> str | None:
        return self._approval_id


class ApprovalController(QObject):
    """Connects the queue to the panel, on the Qt thread.

    The queue is answered from here and nowhere else in the UI, so there is one
    place where a user decision becomes a permission outcome.
    """

    pendingChanged = Signal(int)

    def __init__(
        self, queue: ApprovalQueue, core: object | None = None, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._queue = queue
        self._core = core
        self.panel = ApprovalPanel()
        self.panel.answered.connect(self._on_answered)
        self.panel.stopTaskRequested.connect(self._on_stop_task)

    # -- queue -> UI -------------------------------------------------------
    def refresh(self) -> None:
        """Show the oldest waiting request, or nothing if none is waiting."""
        pending = self._queue.oldest_pending()
        if pending is None:
            self.panel.hide()
        elif pending.approval_id != self.panel.current_approval_id:
            self.panel.show_request(pending)
        self.pendingChanged.emit(len(self._queue.pending()))

    def focus_panel(self) -> bool:
        """Bring the panel forward *and* give it focus (PRD NFR-030).

        Only ever called because the user explicitly asked for it — from the
        tray menu or a keyboard route — so taking focus here is what was
        requested, not focus theft.
        """
        pending = self._queue.oldest_pending()
        if pending is None:
            return False
        if pending.approval_id != self.panel.current_approval_id:
            self.panel.show_request(pending)
        self.panel.show()
        self.panel.raise_()
        self.panel.activateWindow()
        self.panel.setFocus(Qt.FocusReason.ShortcutFocusReason)
        return True

    # -- UI -> queue -------------------------------------------------------
    def _on_answered(
        self,
        approval_id: str,
        decision: Decision,
        scope: GrantScope,
        denial: RememberDenialOption | None,
    ) -> None:
        try:
            self._queue.answer(
                approval_id, decision, scope=scope, remember_denial=denial
            )
        except ValueError:
            # The queue refused the scope. That is the model protecting itself
            # from a defect here; log it loudly rather than retrying narrower.
            _LOG.exception("the approval queue refused a decision from the dialog")
        self.refresh()

    def _on_stop_task(self, approval_id: str) -> None:
        pending = {p.approval_id: p for p in self._queue.pending()}.get(approval_id)
        task_id = pending.request.task_id if pending else None
        if task_id and self._core is not None:
            try:
                self._core.scheduler.cancel(task_id)  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001 - cancelling must not break answering
                _LOG.exception("could not cancel task %s from the approval panel", task_id)
