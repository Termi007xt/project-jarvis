"""The Qt application: wires the core to the tray and the main window.

Everything here runs on the Qt main thread and does no work of its own. Domain
events arrive through :class:`~jarvis.ui.qt_bridge.EventBridge`, already
marshalled onto this thread.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QThread, QTimer
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from jarvis import APP_NAME
from jarvis.config.schema import NetworkMode
from jarvis.core.events.types import (
    ApprovalRequested,
    ApprovalResolved,
    EmergencyStopCompleted,
    Event,
    HealthChecked,
    NetworkModeChanged,
    TaskStateChanged,
)
from jarvis.runtime.core import JarvisCore
from jarvis.runtime.hotkeys import GlobalHotkeys
from jarvis.tasks.states import TaskState
from jarvis.ui.approval import ApprovalController
from jarvis.ui.conversation import ConversationWorker
from jarvis.ui.icons import TrayState
from jarvis.ui.main_window import MainWindow
from jarvis.ui.qt_bridge import EventBridge
from jarvis.ui.tray import JarvisTrayIcon
from jarvis.ui.voice_controller import VoiceController

__all__ = ["JarvisApplication"]

_LOG = logging.getLogger(__name__)


class JarvisApplication(QObject):
    """Composition of core, tray and window."""

    def __init__(self, core: JarvisCore, app: QApplication) -> None:
        super().__init__()
        self._core = core
        self._app = app
        self._app.setApplicationName(APP_NAME)
        self._app.setQuitOnLastWindowClosed(False)  # PRD FR-001: live in the tray

        self.window = MainWindow(core)
        self.tray = JarvisTrayIcon(self)
        self.bridge = EventBridge(core.events, self)
        self._conversation = None
        self._conversation_thread: QThread | None = None
        #: Held deliberately. A worker moved to a thread has no parent QObject,
        #: so without a Python reference PySide6 destroys it as soon as
        #: send_message returns — the thread then starts, emits ``started`` and
        #: finds no receiver, and the turn silently never runs.
        self._conversation_worker: ConversationWorker | None = None
        self._private_session = False
        self._recording = False

        #: The voice stack was built by the core and reported honestly on the
        #: Voice screen, but nothing was ever connected to it. This is that
        #: connection: push-to-talk, the level meter, and the Voice controls.
        self.voice = self._attach_voice()

        # The approval surface exists, so the engine may now ask. Until this
        # line runs, the queue denies everything (ADR-0010).
        self.approvals = ApprovalController(core.approvals, core, self) if core.approvals else None
        if core.approvals is not None:
            core.approvals.set_interactive(True)

        # Only a shell can show a notification, so notify.show is registered
        # now rather than at start-up (ADR-0010).
        core.attach_shell(self._notify_from_tool)

        self.hotkeys = self._register_hotkeys()

        self._connect()
        self.tray.set_network_mode(core.config.network.mode)
        self._apply_state()

        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        else:
            _LOG.warning("no system tray is available; showing the main window instead")
            self.window.show()

        # Refresh the window periodically so task and audit views stay current
        # without every event forcing a repaint.
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(2000)
        self._refresh_timer.timeout.connect(self._refresh_if_visible)
        self._refresh_timer.start()

    # -- voice (PRD FR-013, FR-016, FR-017, FR-018) ------------------------
    def _attach_voice(self) -> object | None:
        """Connect the voice service to the Voice screen and to push-to-talk."""
        voice = getattr(self._core, "voice", None)
        if voice is None:
            return None

        controller = VoiceController(voice, self.window.voice_panel(), self)
        # FR-013: capture may not start without announcing itself.
        voice.set_indicator(self._set_recording_indicator)
        controller.commandHeard.connect(self._on_command_heard)
        controller.noticed.connect(self.tray.notify)
        controller.calibrated.connect(self.window.voice_panel().set_calibration)
        return controller

    def _set_recording_indicator(self, recording: bool) -> None:
        """Runs on the audio thread, so it only queues work onto the GUI one."""
        self._recording = recording
        QTimer.singleShot(0, self._apply_state)

    def _on_command_heard(self, text: str) -> None:
        """A spoken command becomes an ordinary conversation turn."""
        self.show_window("conversation")
        self.send_message(text)

    # -- wiring ------------------------------------------------------------
    def _connect(self) -> None:
        self.tray.openRequested.connect(self.show_window)
        self.tray.settingsRequested.connect(lambda: self.show_window("developer"))
        self.tray.quitRequested.connect(self.quit)
        self.tray.emergencyStopRequested.connect(self.emergency_stop)
        self.tray.offlineModeToggled.connect(self.set_offline_mode)
        self.tray.pauseRequested.connect(self._pause_current)
        self.tray.resumeRequested.connect(self._resume_current)
        self.tray.cancelRequested.connect(self._cancel_current)
        self.tray.reviewApprovalRequested.connect(self.review_pending_approval)

        self.window.emergencyStopRequested.connect(self.emergency_stop)
        self.window.healthCheckRequested.connect(self._run_health_check)
        self.window.approvalAnswered.connect(self._on_window_approval)
        self.window.conversationSendRequested.connect(self.send_message)
        self.window.privateSessionToggled.connect(self.set_private_session)
        self.window.historyClearRequested.connect(self.clear_history)
        self.window.installWakeModelRequested.connect(self.install_wake_model)
        self.window.removeWakeModelRequested.connect(self.remove_wake_model)

        self.bridge.eventReceived.connect(self._on_event)

    # -- event handling ----------------------------------------------------
    def _on_event(self, event: Event) -> None:
        """Runs on the Qt main thread, courtesy of the bridge."""
        if isinstance(event, TaskStateChanged):
            self._apply_state()
            self.window.refresh_tasks()
        elif isinstance(event, HealthChecked):
            self._apply_state()
            self.window.refresh_home()
            self.window.refresh_models()
        elif isinstance(event, NetworkModeChanged):
            self.tray.set_network_mode(NetworkMode(event.current))
            self._apply_state()
        elif isinstance(event, EmergencyStopCompleted):
            self.tray.notify(
                "Automation stopped",
                f"Cancelled {len(event.cancelled_task_ids)} task(s), released "
                f"{len(event.released_locks)} lock(s), stopped "
                f"{len(event.stopped_workers)} worker(s).",
            )
            self._refresh_approvals()
            self._apply_state()
        elif isinstance(event, ApprovalRequested):
            # Impossible to miss is the requirement a non-modal surface has to
            # earn: panel, red tray, notification and a window entry.
            self.tray.notify(
                "Jarvis needs your decision",
                f"{event.action_summary} ({event.risk} risk). "
                "Unanswered requests are denied.",
            )
            self._refresh_approvals()
            self._apply_state()
        elif isinstance(event, ApprovalResolved):
            self._refresh_approvals()
            self._apply_state()
            self.window.refresh_permissions()

    def _refresh_approvals(self) -> None:
        pending = self._core.approvals.pending() if self._core.approvals else ()
        if self.approvals is not None:
            self.approvals.refresh()
        self.tray.set_pending_approvals(len(pending))
        self.window.set_pending_approvals(pending)

    def review_pending_approval(self) -> bool:
        """The keyboard route to a waiting request (PRD NFR-030)."""
        if self.approvals is not None and self.approvals.focus_panel():
            return True
        self.show_window("permissions")
        return False

    def _on_window_approval(self, approval_id: str, allow: bool) -> None:
        """Answered from the Permissions screen rather than the panel."""
        queue = self._core.approvals
        if queue is None:
            return
        from jarvis.core.permissions.models import Decision, GrantScope

        queue.answer(
            approval_id,
            Decision.ALLOW if allow else Decision.DENY,
            scope=GrantScope.ONCE,
        )
        self._refresh_approvals()

    def _apply_state(self) -> None:
        """Derive the tray state from what the runtime is actually doing."""
        config = self._core.config
        if config.network.mode is NetworkMode.OFFLINE:
            state, detail = TrayState.OFFLINE, "Offline mode"
        else:
            state, detail = TrayState.IDLE, "Phase 1: voice and conversation"

        current = self._current_task()
        if current is not None:
            if current.state is TaskState.RUNNING:
                state, detail = TrayState.ACTING, current.name
            elif current.state in (TaskState.QUEUED, TaskState.WAITING):
                state, detail = TrayState.WAITING, current.waiting_on or current.name
            elif current.state in (TaskState.PAUSED, TaskState.AWAITING_APPROVAL):
                state, detail = TrayState.WAITING, f"{current.name} ({current.state.value})"
            elif current.state is TaskState.BLOCKED:
                state, detail = TrayState.BLOCKED, current.blocked_reason or current.name

        health = self._core.last_health
        if health is not None and not health.reachable and not health.skipped:
            state, detail = TrayState.BLOCKED, "Local model runtime unreachable"

        # FR-013: an open microphone is never a quiet state. Recording without a
        # visible indicator is a prohibited capability, not a UI preference.
        if self._recording:
            state, detail = TrayState.RECORDING, "The microphone is open"

        # Last, so it outranks everything: a pending approval is the one state
        # the user must notice, and the tray is how a non-modal surface earns
        # that (ADR-0027).
        if self._core.approvals is not None and self._core.approvals.has_pending:
            state, detail = TrayState.BLOCKED, "Waiting for your approval"

        self.tray.set_state(state, detail)
        self.tray.set_current_task(
            current.task_id if current else None,
            current.name if current else "",
            current.state if current else None,
        )

    def _current_task(self):
        candidates = self._core.tasks.list(
            [
                TaskState.RUNNING,
                TaskState.WAITING,
                TaskState.QUEUED,
                TaskState.PAUSED,
                TaskState.BLOCKED,
                TaskState.AWAITING_APPROVAL,
            ],
            limit=1,
        )
        return candidates[0] if candidates else None

    def _refresh_if_visible(self) -> None:
        # Approvals refresh regardless of window visibility: a request can
        # expire while the window is closed, and the tray must still be right.
        self._refresh_approvals()
        if self.window.isVisible():
            self.window.refresh_all()

    # -- conversation (PRD 9.5, FR-045, FR-046) ---------------------------
    def _ensure_conversation(self):
        """One live conversation at a time, created on first use."""
        if self._conversation is None:
            self._conversation = self._core.start_conversation(
                private=self._private_session
            )
        return self._conversation

    def send_message(self, text: str) -> None:
        """Run one turn on a worker thread; the model call blocks."""
        panel = self.window.conversation_panel()
        if self._conversation_worker is not None:
            # A turn is already in flight. Voice can call this too, so the
            # disabled input is not on its own enough to prevent a second one.
            panel.append_note("Still working on the previous message.")
            return

        engine = self._core.conversation
        if not engine.available:
            panel.append_error(engine.unavailable_reason() or "the model is unavailable")
            return

        panel.append_user(text)
        panel.set_busy(True)

        conversation = self._ensure_conversation()
        thread = QThread(self)
        worker = ConversationWorker(engine, conversation, text)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_turn_finished)
        worker.failed.connect(self._on_turn_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        # Ours first, so the references are released before Qt deletes the
        # thread object. The worker gets no deleteLater: it has no parent, so
        # Python owns it, and asking Qt to delete it too would delete it twice.
        thread.finished.connect(self._on_conversation_thread_finished)
        thread.finished.connect(thread.deleteLater)
        self._conversation_thread = thread
        self._conversation_worker = worker
        thread.start()

    def stop_conversation_thread(self, timeout_ms: int = 5000) -> bool:
        """Stop the in-flight turn's thread before the process goes away.

        Exiting with it still running takes the process down (a native crash,
        not an exception). The wait is bounded because ``run`` may be blocked
        in a model call that ``quit`` cannot interrupt; if it does not stop in
        time we say so rather than hanging the shutdown.
        """
        thread = self._conversation_thread
        if thread is None:
            return True
        thread.quit()
        stopped = thread.wait(timeout_ms)
        if not stopped:
            _LOG.warning(
                "the conversation thread did not stop within %dms; a model call "
                "is probably still running",
                timeout_ms,
            )
        self._conversation_worker = None
        self._conversation_thread = None
        return stopped

    def _on_conversation_thread_finished(self) -> None:
        """Release the worker only once its thread has actually stopped.

        Dropping it in ``_on_turn_finished`` destroyed the C++ object while the
        thread was still shutting down and emitting from it.
        """
        self._conversation_worker = None
        self._conversation_thread = None

    def _on_turn_finished(self, turn: object) -> None:
        panel = self.window.conversation_panel()
        panel.set_busy(False)
        if not getattr(turn, "ok", False):
            panel.append_error(getattr(turn, "error", "") or "no answer")
        else:
            panel.append_reply(turn.reply, turn.label)  # type: ignore[attr-defined]
            for refusal in getattr(turn, "refused_proposals", ()):
                panel.append_note(refusal)
            review = getattr(turn, "review", None)
            if review is not None and review.amended:
                panel.append_note(review.note or "")
        self.window.refresh_conversation()

    def _on_turn_failed(self, message: str) -> None:
        panel = self.window.conversation_panel()
        panel.set_busy(False)
        panel.append_error(message)

    def set_private_session(self, private: bool) -> None:
        """Switching mid-conversation ends the current one (PRD FR-046)."""
        self._private_session = private
        if self._conversation is not None:
            self._core.history.end(self._conversation.conversation_id)
            self._conversation = None
        panel = self.window.conversation_panel()
        panel.clear_transcript()
        panel.set_private(private)
        if not private:
            panel.append_note("History is being recorded again.")

    def clear_history(self) -> None:
        removed = self._core.history.delete_all()
        self.window.conversation_panel().append_note(
            f"Deleted {removed} conversation(s) from history."
        )

    # -- wake-model bootstrap (ADR-0016, PRD 17.2) ------------------------
    def install_wake_model(self) -> None:
        """The GUI half of the one-time install. Downloads, then verifies."""
        from jarvis.audio.wake_install import install_wake_model

        panel = self.window.voice_panel()
        panel.install_model_button.setEnabled(False)
        panel.set_model_state(
            self._core.paths.root / "models" / "wake", False, "Downloading…"
        )
        # Blocking, but bounded and user-initiated; the button is disabled
        # meanwhile so it cannot be started twice.
        report = install_wake_model(self._core.paths.root)
        panel.install_model_button.setEnabled(True)
        self.tray.notify("Wake-word model", report.describe())
        self.window.refresh_voice()

    def remove_wake_model(self) -> None:
        from jarvis.audio.wake_install import uninstall_wake_model

        removed, directory = uninstall_wake_model(self._core.paths.root)
        self.tray.notify(
            "Wake-word model",
            f"Removed from {directory}." if removed else f"Nothing to remove in {directory}.",
        )
        self.window.refresh_voice()

    def _notify_from_tool(self, title: str, message: str) -> bool:
        """Backs the ``notify.show`` tool. Runs on whichever thread calls it."""
        try:
            QTimer.singleShot(0, lambda: self.tray.notify(title, message))
        except Exception:  # noqa: BLE001 - the tool reports failure honestly
            _LOG.exception("could not show a notification")
            return False
        return True

    # -- hotkeys (PRD 11.3, FR-018) ---------------------------------------
    def _register_hotkeys(self) -> GlobalHotkeys:
        """Emergency stop and push-to-talk, both configurable.

        Hotkey callbacks arrive on the hotkey thread, so they only ever queue
        work onto the Qt thread — touching widgets from there would be a
        cross-thread violation Qt would not survive.
        """
        config = self._core.config
        hotkeys = GlobalHotkeys()
        hotkeys.add(
            "emergency_stop",
            config.ui.emergency_stop_hotkey,
            lambda: QTimer.singleShot(0, self.emergency_stop_from_hotkey),
        )
        hotkeys.add(
            "push_to_talk",
            config.audio.wake_word.push_to_talk_hotkey,
            lambda: QTimer.singleShot(0, self.push_to_talk),
        )
        hotkeys.start()

        for binding in hotkeys.unavailable():
            # Never silently missing: the user asked for this key and did not
            # get it, and only they can resolve the conflict (ADR-0010).
            _LOG.warning("hotkey unavailable — %s", binding.describe())
        return hotkeys

    def emergency_stop_from_hotkey(self) -> None:
        report = self._core.emergency_stop(origin="hotkey")
        _LOG.info("emergency stop via hotkey: %s", report.describe())

    def push_to_talk(self) -> None:
        """F9. Press to start speaking, press again to cut it short.

        Not hold-to-talk: ``RegisterHotKey`` reports the press only, so there is
        no release to react to. Speech usually ends on its own when the voice
        activity detector hears silence.
        """
        toggle = getattr(self.voice, "toggle_push_to_talk", None)
        if toggle is not None:
            toggle()
            return
        self.tray.notify(
            "Push to talk is not ready",
            "The voice stack is not available on this machine yet. "
            "The Voice screen explains what is missing.",
        )

    # -- actions -----------------------------------------------------------
    def show_window(self, area: str | None = None) -> None:
        if area:
            self.window.show_area(area)
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        self.window.refresh_all()

    def emergency_stop(self) -> None:
        report = self._core.emergency_stop(origin="tray")
        _LOG.info("emergency stop: %s", report.describe())

    def set_offline_mode(self, offline: bool) -> None:
        mode = NetworkMode.OFFLINE if offline else NetworkMode.LOCAL_ASSISTANT
        if self._core.config.network.mode is mode:
            return
        self._core.set_network_mode(mode)
        self._apply_state()
        self.window.refresh_all()

    def _run_health_check(self) -> None:
        self._core.run_health_check_task()

    def _pause_current(self) -> None:
        task_id = self.tray.current_task_id
        if task_id:
            self._core.scheduler.pause(task_id)

    def _resume_current(self) -> None:
        task_id = self.tray.current_task_id
        if task_id:
            self._core.scheduler.resume(task_id)

    def _cancel_current(self) -> None:
        task_id = self.tray.current_task_id
        if task_id:
            self._core.scheduler.cancel(task_id)

    def quit(self) -> None:
        self._refresh_timer.stop()
        self.stop_conversation_thread()
        shutdown = getattr(self.voice, "shutdown", None)
        if shutdown is not None:
            shutdown()
        self.bridge.detach()
        self.hotkeys.stop()
        if self.approvals is not None:
            self.approvals.panel.hide()
        self.tray.hide()
        self._core.shutdown("quit from the tray menu")
        self._app.quit()
