"""Main window: the fifteen navigation areas of PRD section 9.3.

Six areas are live against real data. The rest render an honest "not
implemented" panel naming the phase that delivers them (ADR-0010). No panel
fabricates data, and no panel reports a capability the runtime does not have.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from jarvis import APP_NAME, APP_VERSION
from jarvis.core.audit.models import AuditCategory
from jarvis.runtime.core import JarvisCore
from jarvis.tasks.states import TaskState

__all__ = ["MainWindow", "NAV_AREAS", "NavArea"]


@dataclass(frozen=True)
class NavArea:
    key: str
    title: str
    phase: int
    live: bool
    note: str = ""


#: PRD section 9.3, in order. ``live`` means the panel shows real runtime data.
NAV_AREAS: tuple[NavArea, ...] = (
    NavArea("home", "Home", 0, True),
    NavArea("conversation", "Conversation", 1, True),
    NavArea("tasks", "Tasks", 0, True),
    NavArea("skills", "Skills", 3, False, "Recorded and editable reusable workflows."),
    NavArea("memory", "Memory", 3, False, "Reviewable memories and memory candidates."),
    NavArea("applications", "Applications", 2, False,
            "The application catalogue, aliases and launch verification."),
    NavArea("models", "Models", 0, True),
    NavArea("voice", "Voice", 1, True),
    NavArea("permissions", "Permissions", 0, True),
    NavArea("integrations", "Integrations", 6, False,
            "Optional external providers, configured with your own keys."),
    NavArea("history", "History", 1, False, "Conversation history and its retention controls."),
    NavArea("audit", "Audit log", 0, True),
    NavArea("import_export", "Import / Export", 3, False,
            "Portable identity packages (.jarvispack)."),
    NavArea("developer", "Developer tools", 0, True),
    NavArea("about", "About and updates", 0, True),
)


class _NotImplementedPanel(QWidget):
    """Says exactly what is missing and when it arrives. Never a fake screen."""

    def __init__(self, area: NavArea, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        heading = QLabel(area.title)
        heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(heading)

        status = QLabel(f"Not implemented yet — planned for Phase {area.phase}.")
        status.setStyleSheet("font-weight: 600;")
        layout.addWidget(status)

        if area.note:
            note = QLabel(area.note)
            note.setWordWrap(True)
            layout.addWidget(note)

        explanation = QLabel(
            "This screen is shown, and disabled, on purpose. Project Jarvis does not "
            "display placeholder screens that appear to work. See docs/BACKLOG.md for "
            "what this phase delivers, and ADR-0010 for why unavailable features are "
            "visible rather than hidden."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: palette(mid);")
        layout.addWidget(explanation)
        layout.addStretch(1)


class _TextPanel(QWidget):
    """A heading, a refresh button and a read-only text area."""

    refreshRequested = Signal()

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QHBoxLayout()
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        header.addWidget(heading)
        header.addStretch(1)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setAccessibleName(f"Refresh {title}")
        self.refresh_button.clicked.connect(self.refreshRequested.emit)
        header.addWidget(self.refresh_button)
        layout.addLayout(header)

        self.body = QPlainTextEdit()
        self.body.setReadOnly(True)
        self.body.setAccessibleName(f"{title} contents")
        layout.addWidget(self.body, 1)

    def set_text(self, text: str) -> None:
        self.body.setPlainText(text)


class _TablePanel(QWidget):
    refreshRequested = Signal()

    def __init__(self, title: str, columns: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QHBoxLayout()
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        header.addWidget(heading)
        header.addStretch(1)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setAccessibleName(f"Refresh {title}")
        self.refresh_button.clicked.connect(self.refreshRequested.emit)
        header.addWidget(self.refresh_button)
        layout.addLayout(header)

        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setAccessibleName(f"{title} table")
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        self.empty_label = QLabel("")
        self.empty_label.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.empty_label)

    def set_rows(self, rows: list[list[str]], empty_message: str = "Nothing to show.") -> None:
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))
        self.empty_label.setText(empty_message if not rows else "")


class _PermissionsPanel(QWidget):
    """Active grants, and any approval currently waiting for an answer.

    The panel exists because ADR-0027's approval surface is non-modal: a request
    the user dismissed or never saw must still be findable and answerable, with
    a keyboard, from inside the window.
    """

    refreshRequested = Signal()
    answered = Signal(str, bool)  # approval_id, allow

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QHBoxLayout()
        heading = QLabel("Permissions")
        heading.setStyleSheet("font-size: 20px; font-weight: 600;")
        header.addWidget(heading)
        header.addStretch(1)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setAccessibleName("Refresh Permissions")
        self.refresh_button.clicked.connect(self.refreshRequested.emit)
        header.addWidget(self.refresh_button)
        layout.addLayout(header)

        self.pending_heading = QLabel("Waiting for your decision")
        self.pending_heading.setStyleSheet("font-weight: 600;")
        layout.addWidget(self.pending_heading)

        self.pending_list = QListWidget()
        self.pending_list.setAccessibleName("Pending approvals")
        self.pending_list.setMaximumHeight(120)
        layout.addWidget(self.pending_list)

        actions = QHBoxLayout()
        self.allow_button = QPushButton("Allow once")
        self.allow_button.setAccessibleName("Allow the selected request once")
        self.allow_button.clicked.connect(lambda: self._answer(True))
        self.deny_button = QPushButton("Deny")
        self.deny_button.setAccessibleName("Deny the selected request")
        self.deny_button.clicked.connect(lambda: self._answer(False))
        actions.addWidget(self.allow_button)
        actions.addWidget(self.deny_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Capability", "Risk", "Decision", "Scope", "Scope reference", "Granted by"]
        )
        self.table.setAccessibleName("Permission grants table")
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        self.empty_label = QLabel("")
        self.empty_label.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.empty_label)

        self.set_pending(())

    def set_rows(self, rows: list[list[str]], empty_message: str = "Nothing to show.") -> None:
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))
        self.empty_label.setText(empty_message if not rows else "")

    def set_pending(self, pending: tuple[object, ...]) -> None:
        selected = self.selected_approval_id()
        self.pending_list.clear()
        for entry in pending:
            request = entry.request  # type: ignore[attr-defined]
            item = QListWidgetItem(
                f"{request.action_summary}  ·  {request.risk.value} risk  ·  "
                f"{int(entry.seconds_remaining())}s left"  # type: ignore[attr-defined]
            )
            item.setData(Qt.ItemDataRole.UserRole, request.approval_id)
            self.pending_list.addItem(item)
            if request.approval_id == selected:
                self.pending_list.setCurrentItem(item)

        waiting = bool(pending)
        if waiting and self.pending_list.currentItem() is None:
            self.pending_list.setCurrentRow(0)
        self.pending_heading.setText(
            "Waiting for your decision" if waiting else "Nothing is waiting for a decision"
        )
        self.pending_list.setVisible(waiting)
        self.allow_button.setEnabled(waiting)
        self.deny_button.setEnabled(waiting)

    def selected_approval_id(self) -> str | None:
        item = self.pending_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else None

    def _answer(self, allow: bool) -> None:
        approval_id = self.selected_approval_id()
        if approval_id:
            self.answered.emit(approval_id, allow)


class MainWindow(QMainWindow):
    """Navigation shell over live core state."""

    emergencyStopRequested = Signal()
    healthCheckRequested = Signal()
    approvalAnswered = Signal(str, bool)
    conversationSendRequested = Signal(str)
    privateSessionToggled = Signal(bool)
    historyClearRequested = Signal()

    def __init__(self, core: JarvisCore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._core = core
        self.setWindowTitle(f"{APP_NAME} (internal codename Jarvis)")
        self.resize(1100, 720)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.nav = QListWidget()
        self.nav.setFixedWidth(220)
        self.nav.setAccessibleName("Navigation")
        layout.addWidget(self.nav)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self._panels: dict[str, QWidget] = {}
        self._build_panels()
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)
        self.refresh_all()

    # -- construction ------------------------------------------------------
    def _build_panels(self) -> None:
        for area in NAV_AREAS:
            item = QListWidgetItem(area.title if area.live else f"{area.title}  ·  Phase {area.phase}")
            item.setToolTip(
                area.title if area.live else f"Not implemented — planned for Phase {area.phase}."
            )
            if not area.live:
                item.setForeground(Qt.GlobalColor.gray)
            self.nav.addItem(item)

            panel = self._live_panel(area) if area.live else _NotImplementedPanel(area)
            self._panels[area.key] = panel
            self.stack.addWidget(panel)

    def _live_panel(self, area: NavArea) -> QWidget:
        if area.key == "voice":
            from jarvis.ui.voice import VoicePanel

            return VoicePanel()
        if area.key == "conversation":
            from jarvis.ui.conversation import ConversationPanel

            panel = ConversationPanel(self._core)
            panel.sendRequested.connect(self.conversationSendRequested.emit)
            panel.privateSessionToggled.connect(self.privateSessionToggled.emit)
            panel.historyCleared.connect(self.historyClearRequested.emit)
            return panel
        if area.key == "home":
            panel = _TextPanel("Home")
            panel.refreshRequested.connect(self.refresh_all)
            stop = QPushButton("Emergency stop all automation")
            stop.setAccessibleName("Emergency stop all automation")
            stop.clicked.connect(self.emergencyStopRequested.emit)
            check = QPushButton("Run a health check")
            check.setAccessibleName("Run a health check")
            check.clicked.connect(self.healthCheckRequested.emit)
            row = QHBoxLayout()
            row.addWidget(check)
            row.addWidget(stop)
            row.addStretch(1)
            panel.layout().addLayout(row)  # type: ignore[union-attr]
            return panel
        if area.key == "tasks":
            panel = _TablePanel(
                "Tasks",
                ["Name", "State", "Attempts", "Locks", "Waiting on", "Result"],
            )
            panel.refreshRequested.connect(self.refresh_tasks)
            return panel
        if area.key == "permissions":
            panel = _PermissionsPanel()
            panel.refreshRequested.connect(self.refresh_permissions)
            panel.answered.connect(self.approvalAnswered.emit)
            return panel
        if area.key == "audit":
            panel = _TablePanel("Audit log", ["Time", "Category", "Actor", "Summary", "Result"])
            panel.refreshRequested.connect(self.refresh_audit)
            return panel
        if area.key == "models":
            panel = _TextPanel("Models")
            panel.refreshRequested.connect(self.refresh_models)
            return panel
        if area.key == "developer":
            panel = _TextPanel("Developer tools")
            panel.refreshRequested.connect(self.refresh_developer)
            return panel
        panel = _TextPanel("About and updates")
        panel.refreshRequested.connect(self.refresh_about)
        return panel

    # -- refresh -----------------------------------------------------------
    def refresh_all(self) -> None:
        self.refresh_home()
        self.refresh_conversation()
        self.refresh_voice()
        self.refresh_tasks()
        self.refresh_permissions()
        self.refresh_audit()
        self.refresh_models()
        self.refresh_developer()
        self.refresh_about()

    def refresh_voice(self) -> None:
        """Report the voice stack exactly as it is (ADR-0010, FR-011)."""
        from jarvis.audio.availability import describe_voice_stack
        from jarvis.audio.capture import list_devices
        from jarvis.audio.wake import wake_model_path

        panel = self.voice_panel()
        config = self._core.config
        panel.set_stack_status(
            describe_voice_stack(config, wake_model_path(self._core.paths.root))
        )
        panel.set_phrase(
            config.audio.wake_word.phrase, enrolled=config.audio.wake_word.enrolled
        )

        voice = getattr(self._core, "voice", None)
        if voice is not None:
            panel.set_voices(tuple(voice.tts.voices()))
            panel.set_duplex(voice.pipeline.duplex.describe_mode())
            panel.set_enrolment(
                voice.enrolment_summary(),
                passed=voice.enrolment_passed,
                enrolled=config.audio.wake_word.enrolled,
            )
        else:
            panel.set_enrolment(
                "The voice stack is not running, so no enrolment has been measured.",
                passed=False,
                enrolled=False,
            )
        panel.set_devices(list_devices(inputs_only=True))

    def voice_panel(self):
        from jarvis.ui.voice import VoicePanel

        panel = self._panels["voice"]
        assert isinstance(panel, VoicePanel)
        return panel

    def refresh_conversation(self) -> None:
        panel = self.conversation_panel()
        engine = getattr(self._core, "conversation", None)
        if engine is None:
            panel.set_availability(False, "The conversation engine is not running.")
            return
        panel.set_availability(engine.available, engine.unavailable_reason())

    def refresh_home(self) -> None:
        status = self._core.status()
        health = status.last_health
        recovery = status.recovery
        lines = [
            f"Status                 {'running' if status.running else 'stopped'}",
            f"Version                {status.app_version}",
            f"Network mode           {status.network_mode}",
            f"Data vault             {status.vault_root}",
            f"Database schema        v{status.schema_version}",
            "",
            f"Registered tools       {', '.join(status.registered_tools) or 'none'}",
            f"Active tasks           {status.active_tasks}",
            f"Held resource locks    {', '.join(status.held_locks) or 'none'}",
            f"Running workers        {', '.join(status.workers) or 'none'}",
            "",
            f"Local model runtime    {health.describe() if health else 'not checked yet'}",
            f"Startup recovery       {recovery.describe() if recovery else 'not run'}",
        ]

        secrets = getattr(self._core, "secrets", None)
        if secrets is not None:
            lines.append(
                f"Protected secrets      "
                f"{'available' if secrets.available else secrets.unavailable_reason()}"
            )

        engine = getattr(self._core, "conversation", None)
        if engine is not None:
            lines.append(
                f"Conversation           "
                f"{'ready' if engine.available else (engine.unavailable_reason() or 'unavailable')}"
            )

        from jarvis.audio.availability import describe_voice_stack

        voice = describe_voice_stack(self._core.config)
        lines += ["", "Voice stack", "-----------"]
        lines += [f"  {component.describe()}" for component in voice.components]

        lines += [
            "",
            "Phase 1 adds voice and conversation. It performs no desktop or browser",
            "automation beyond opening an approved application or URL, and has no",
            "filesystem tools, screen capture or clipboard access.",
        ]
        self._text("home").set_text("\n".join(lines))

    def refresh_tasks(self) -> None:
        tasks = self._core.tasks.list(limit=200)
        rows = [
            [
                task.name,
                task.state.value + (" (recovered)" if task.recovered else ""),
                f"{task.attempts}/{task.max_retries + 1}",
                ", ".join(task.required_locks) or "—",
                task.waiting_on or task.blocked_reason or "—",
                task.result_summary or task.failure_code or "—",
            ]
            for task in tasks
        ]
        self._table("tasks").set_rows(rows, "No tasks yet.")

    def refresh_permissions(self) -> None:
        from jarvis.core.permissions.catalogue import CAPABILITIES

        grants = self._core.permissions.list_grants(active_only=True)
        rows = []
        for grant in grants:
            capability = CAPABILITIES.get(grant.capability_id)
            rows.append(
                [
                    grant.capability_id,
                    capability.risk.value if capability is not None else "unknown",
                    grant.decision.value,
                    grant.scope.value,
                    grant.scope_ref or "—",
                    grant.created_by,
                ]
            )
        self._permissions_panel().set_rows(
            rows,
            "No active permission grants. Every capability will ask before it runs.",
        )

    def set_pending_approvals(self, pending: tuple[object, ...]) -> None:
        self._permissions_panel().set_pending(pending)

    def refresh_audit(self) -> None:
        records = self._core.audit.query(limit=300)
        rows = [
            [
                str(record.get("occurred_at", ""))[:19].replace("T", " "),
                str(record.get("category", "")),
                str(record.get("actor", "")),
                str(record.get("summary", "")),
                str(record.get("result") or record.get("error") or "—"),
            ]
            for record in records
        ]
        self._table("audit").set_rows(rows, "No audit records yet.")

    def refresh_models(self) -> None:
        config = self._core.config
        health = self._core.last_health
        lines = [
            "Configured model roles (PRD FR-041). Nothing here is hard-coded;",
            "every role names a profile in configuration.",
            "",
            f"  Planner / conversation   {config.models.planner.name}"
            f"  (context {config.models.planner.context_length})",
            f"  Vision                   {config.models.vision.name}"
            f"  (context {config.models.vision.context_length})",
            f"  Embeddings               {config.models.embeddings.name}"
            f"  (context {config.models.embeddings.context_length})",
            "",
            f"  Load strategy            {config.model_runtime.load_strategy}",
            f"  Idle unload              {config.model_runtime.idle_unload_seconds}s",
            f"  Parallel heavy models    {config.model_runtime.allow_parallel_heavy_models}",
            "",
            f"Endpoint                   {config.llm.ollama.base_url}"
            f" (loopback required: {config.llm.ollama.require_loopback})",
            f"Last health check          {health.describe() if health else 'not checked yet'}",
        ]
        if health and health.reachable:
            lines += ["", "Installed in the local runtime:"]
            lines += [f"  {name}" for name in health.models] or ["  (none reported)"]
            if health.models and self._core.last_health:
                pass
        lines += [
            "",
            "Installing, removing and testing models is a Phase 1 and Phase 6 capability.",
            "Phase 0 reads this state; it does not change it.",
        ]
        self._text("models").set_text("\n".join(lines))

    def refresh_developer(self) -> None:
        registry = self._core.registry
        scheduler_status = self._core.scheduler.status()
        lines = [
            "Registered tools",
            "----------------",
        ]
        for spec in registry.specs():
            lines += [
                f"  {spec.tool_id} v{spec.version}   risk={spec.risk.value}"
                f"  changes_state={spec.changes_state}",
                f"    capabilities: {', '.join(spec.required_capabilities)}",
                f"    locks:        {', '.join(spec.resource_locks) or 'none'}",
                f"    timeout:      {spec.timeout_seconds}s"
                f"   retries: {spec.retry_policy.max_attempts}",
                f"    failures:     {', '.join(spec.failure_codes)}",
                f"    verification: {spec.verification}",
            ]
        lines += [
            "",
            "Scheduler",
            "---------",
            f"  running          {scheduler_status['running']}",
            f"  max concurrent   {scheduler_status['max_concurrent']}",
            f"  in flight        {scheduler_status['in_flight'] or 'none'}",
            f"  runners          {', '.join(scheduler_status['registered_runners'])}",
            f"  held locks       {scheduler_status['held_locks'] or 'none'}",
            "",
            "Configuration overrides (the diff from shipped defaults)",
            "-------------------------------------------------------",
            repr(self._core.config_store.user_overrides()) or "  none",
            "",
            f"Defaults file: {self._core.config_store.defaults_path}",
            f"User file:     {self._core.config_store.user_config_path}",
            f"Audit log:     {self._core.audit.path}",
        ]
        self._text("developer").set_text("\n".join(lines))

    def refresh_about(self) -> None:
        lines = [
            f"{APP_NAME} {APP_VERSION}",
            "",
            "\"Jarvis\" is an internal codename only. The public product name is an",
            "open decision (docs/decisions/ADR-0011-public-product-name.md).",
            "",
            "This build is Phase 0: foundation and safety architecture.",
            "It contains no voice input or output, no desktop or browser automation,",
            "no filesystem tools, no screen capture and no clipboard access.",
            "",
            "It has no generic shell, PowerShell, Command Prompt, WSL or",
            "arbitrary-code-execution capability, and a build test fails if one is",
            "ever introduced (ADR-0003).",
            "",
            "Update checking is a Phase 6 capability and is not implemented.",
            "",
            "Documents: ARCHITECTURE.md, SECURITY.md, THREAT_MODEL.md, DATA_MODEL.md,",
            "docs/BACKLOG.md, docs/decisions/",
        ]
        self._text("about").set_text("\n".join(lines))

    # -- helpers -----------------------------------------------------------
    def _text(self, key: str) -> _TextPanel:
        panel = self._panels[key]
        assert isinstance(panel, _TextPanel)
        return panel

    def _table(self, key: str) -> _TablePanel:
        panel = self._panels[key]
        assert isinstance(panel, _TablePanel)
        return panel

    def _permissions_panel(self) -> _PermissionsPanel:
        panel = self._panels["permissions"]
        assert isinstance(panel, _PermissionsPanel)
        return panel

    def conversation_panel(self):
        from jarvis.ui.conversation import ConversationPanel

        panel = self._panels["conversation"]
        assert isinstance(panel, ConversationPanel)
        return panel

    def show_area(self, key: str) -> None:
        for index, area in enumerate(NAV_AREAS):
            if area.key == key:
                self.nav.setCurrentRow(index)
                return

    def live_area_keys(self) -> tuple[str, ...]:
        return tuple(area.key for area in NAV_AREAS if area.live)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt naming
        """Closing the window leaves Jarvis running in the tray (PRD FR-001)."""
        event.ignore()
        self.hide()
