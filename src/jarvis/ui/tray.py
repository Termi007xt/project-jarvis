"""System tray icon and menu (PRD sections 9.1 and 9.2).

Menu entries whose feature does not exist yet are present but disabled, with a
tooltip naming the phase that delivers them (ADR-0010). They are not hidden, so
the shape of the product is visible, and not wired to a stub, so nothing can
report a success it did not achieve.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from jarvis import APP_NAME
from jarvis.config.schema import NetworkMode
from jarvis.tasks.states import TaskState
from jarvis.ui.icons import TrayState, tray_icon

__all__ = ["JarvisTrayIcon"]

#: Menu items from PRD section 9.2 with no implementation yet. Shown, disabled,
#: and honest about why.
_UNAVAILABLE: dict[str, str] = {
    "listening": "Wake-phrase listening arrives in Phase 1 (voice-first assistant).",
    "push_to_talk": "Push to talk arrives in Phase 1 (voice-first assistant).",
    "mute_voice": "Voice output arrives in Phase 1 (voice-first assistant).",
}


class JarvisTrayIcon(QObject):
    """Tray presence, state indication and quick controls."""

    openRequested = Signal()
    settingsRequested = Signal()
    quitRequested = Signal()
    emergencyStopRequested = Signal()
    pauseRequested = Signal()
    resumeRequested = Signal()
    cancelRequested = Signal()
    reviewApprovalRequested = Signal()
    offlineModeToggled = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._state = TrayState.IDLE
        self._current_task_id: str | None = None
        self._pending_approvals = 0

        self._icon = QSystemTrayIcon(tray_icon(TrayState.IDLE), self)
        self._menu = QMenu()
        self._build_menu()
        self._icon.setContextMenu(self._menu)
        self._icon.activated.connect(self._on_activated)
        self.set_state(TrayState.IDLE, "Starting up")

    # -- construction ------------------------------------------------------
    def _build_menu(self) -> None:
        self.action_open = self._add(self._menu, "&Open Jarvis", self.openRequested.emit)

        # A non-modal approval surface must be reachable without a mouse
        # (PRD NFR-030, ADR-0027). This entry is that route.
        self.action_review_approval = self._add(
            self._menu, "&Review pending approval", self.reviewApprovalRequested.emit
        )
        self.action_review_approval.setEnabled(False)
        self.action_review_approval.setToolTip("No approval is waiting.")
        self._menu.addSeparator()

        self.action_listening = self._add(self._menu, "Listening", None, key="listening")
        self.action_listening.setCheckable(True)
        self.action_push_to_talk = self._add(
            self._menu, "Push to talk", None, key="push_to_talk"
        )
        self._menu.addSeparator()

        self.action_current_task = QAction("Current task: none", self._menu)
        self.action_current_task.setEnabled(False)
        self.action_current_task.setToolTip("The task currently holding Jarvis's attention.")
        self._menu.addAction(self.action_current_task)

        self.action_pause = self._add(self._menu, "&Pause current task", self.pauseRequested.emit)
        self.action_resume = self._add(self._menu, "&Resume current task", self.resumeRequested.emit)
        self.action_cancel = self._add(self._menu, "&Cancel current task", self.cancelRequested.emit)
        for action in (self.action_pause, self.action_resume, self.action_cancel):
            action.setEnabled(False)
        self._menu.addSeparator()

        self.action_emergency_stop = self._add(
            self._menu, "&Emergency stop all automation", self.emergencyStopRequested.emit
        )
        self.action_emergency_stop.setToolTip(
            "Cancel every running task, release every resource lock and stop all "
            "automation workers. Jarvis keeps running."
        )
        self._menu.addSeparator()

        self.action_mute = self._add(self._menu, "Mute voice", None, key="mute_voice")
        self.action_mute.setCheckable(True)

        self.action_offline = QAction("&Offline mode", self._menu)
        self.action_offline.setCheckable(True)
        self.action_offline.setToolTip(
            "Make no network request at all. Local inference only."
        )
        self.action_offline.toggled.connect(self.offlineModeToggled.emit)
        self._menu.addAction(self.action_offline)
        self._menu.addSeparator()

        self.action_settings = self._add(self._menu, "&Settings", self.settingsRequested.emit)
        self.action_quit = self._add(self._menu, "&Quit", self.quitRequested.emit)

    def _add(self, menu: QMenu, text: str, slot: object, key: str | None = None) -> QAction:
        action = QAction(text, menu)
        if key is not None:
            action.setEnabled(False)
            action.setToolTip(_UNAVAILABLE[key])
            action.setText(f"{text} (Phase 1)")
        elif slot is not None:
            action.triggered.connect(slot)  # type: ignore[arg-type]
        menu.addAction(action)
        return action

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.openRequested.emit()

    # -- state -------------------------------------------------------------
    def set_state(self, state: TrayState, detail: str = "") -> None:
        """Colour, shape, tooltip and accessible name all change together."""
        self._state = state
        self._icon.setIcon(tray_icon(state))
        suffix = f" — {detail}" if detail else ""
        tooltip = f"{APP_NAME}: {state.label}{suffix}"
        self._icon.setToolTip(tooltip)
        # Screen readers announce this; colour is never the only signal.
        self._icon.setProperty("accessibleName", tooltip)

    @property
    def state(self) -> TrayState:
        return self._state

    def set_pending_approvals(self, count: int) -> None:
        """Enable the keyboard route and say how many are waiting."""
        self._pending_approvals = count
        self.action_review_approval.setEnabled(count > 0)
        if count > 0:
            self.action_review_approval.setText(
                f"&Review pending approval ({count})" if count > 1 else "&Review pending approval"
            )
            self.action_review_approval.setToolTip(
                "Jarvis is waiting for your decision. Unanswered requests are denied."
            )
        else:
            self.action_review_approval.setText("&Review pending approval")
            self.action_review_approval.setToolTip("No approval is waiting.")

    @property
    def pending_approvals(self) -> int:
        return self._pending_approvals

    def set_network_mode(self, mode: NetworkMode) -> None:
        blocked = self.action_offline.blockSignals(True)
        self.action_offline.setChecked(mode is NetworkMode.OFFLINE)
        self.action_offline.blockSignals(blocked)

    def set_current_task(self, task_id: str | None, name: str = "", state: TaskState | None = None) -> None:
        self._current_task_id = task_id
        if task_id is None:
            self.action_current_task.setText("Current task: none")
            self.action_pause.setEnabled(False)
            self.action_resume.setEnabled(False)
            self.action_cancel.setEnabled(False)
            return

        label = state.value if state is not None else "unknown"
        self.action_current_task.setText(f"Current task: {name} ({label})")
        self.action_pause.setEnabled(
            state in (TaskState.QUEUED, TaskState.RUNNING, TaskState.WAITING)
        )
        self.action_resume.setEnabled(state in (TaskState.PAUSED, TaskState.BLOCKED))
        self.action_cancel.setEnabled(state is not None and state not in (
            TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED
        ))

    @property
    def current_task_id(self) -> str | None:
        return self._current_task_id

    # -- presence ----------------------------------------------------------
    def show(self) -> None:
        self._icon.show()

    def hide(self) -> None:
        self._icon.hide()

    def notify(self, title: str, message: str, seconds: int = 5) -> None:
        self._icon.showMessage(title, message, self._icon.icon(), seconds * 1000)

    @property
    def system_tray_icon(self) -> QSystemTrayIcon:
        return self._icon

    @property
    def menu(self) -> QMenu:
        return self._menu
