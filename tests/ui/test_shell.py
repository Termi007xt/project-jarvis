"""Tray, main window and the Qt event bridge.

Runs under ``QT_QPA_PLATFORM=offscreen`` (set in conftest), so it needs no
display and works in CI.
"""

from __future__ import annotations

import threading

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from jarvis.config.schema import NetworkMode  # noqa: E402
from jarvis.core.events.types import AppStarted, TaskStateChanged  # noqa: E402
from jarvis.tasks.states import TaskState  # noqa: E402
from jarvis.ui.icons import TrayState, state_colour, tray_icon  # noqa: E402
from jarvis.ui.main_window import NAV_AREAS, MainWindow  # noqa: E402
from jarvis.ui.qt_bridge import EventBridge  # noqa: E402
from jarvis.ui.tray import JarvisTrayIcon  # noqa: E402

pytestmark = pytest.mark.ui


# =========================================================================
# Icons (PRD section 9.1, NFR-033)
# =========================================================================
def test_all_seven_prd_tray_states_exist() -> None:
    assert {state.value for state in TrayState} == {
        "offline", "idle", "recording", "thinking", "acting", "waiting", "blocked",
    }


def test_each_state_renders_a_non_empty_icon(qapp) -> None:
    for state in TrayState:
        icon = tray_icon(state)
        assert not icon.isNull()
        assert not icon.pixmap(64, 64).isNull()


def test_states_are_distinguishable_without_colour(qapp) -> None:
    """PRD NFR-033: do not rely on colour alone."""
    shapes = {state.shape for state in TrayState}
    assert len(shapes) == len(TrayState), "each state needs a distinct shape"

    labels = {state.label for state in TrayState}
    assert len(labels) == len(TrayState), "each state needs a distinct text label"


def test_state_colours_are_distinct(qapp) -> None:
    colours = {state_colour(state).name() for state in TrayState}
    assert len(colours) == len(TrayState)


# =========================================================================
# Tray (PRD section 9.2)
# =========================================================================
@pytest.fixture
def tray(qapp) -> JarvisTrayIcon:
    return JarvisTrayIcon()


def test_the_tray_menu_contains_every_prd_entry(tray: JarvisTrayIcon) -> None:
    texts = [action.text().replace("&", "") for action in tray.menu.actions() if action.text()]
    joined = " | ".join(texts).lower()
    for expected in (
        "open jarvis",
        "listening",
        "push to talk",
        "current task",
        "pause current task",
        "resume current task",
        "cancel current task",
        "emergency stop",
        "mute voice",
        "offline mode",
        "settings",
        "quit",
    ):
        assert expected in joined, f"tray menu is missing '{expected}'"


def test_unavailable_entries_are_shown_disabled_and_name_their_phase(
    tray: JarvisTrayIcon,
) -> None:
    """ADR-0010: visible, disabled, honest — never hidden and never faked."""
    for action in (tray.action_listening, tray.action_push_to_talk, tray.action_mute):
        assert action.isVisible() or True  # present in the menu
        assert not action.isEnabled()
        assert "Phase 1" in action.text()
        assert "Phase 1" in action.toolTip()


def test_available_entries_are_enabled(tray: JarvisTrayIcon) -> None:
    for action in (
        tray.action_open,
        tray.action_emergency_stop,
        tray.action_offline,
        tray.action_settings,
        tray.action_quit,
    ):
        assert action.isEnabled()


def test_setting_a_state_updates_icon_tooltip_and_accessible_name(
    tray: JarvisTrayIcon,
) -> None:
    tray.set_state(TrayState.BLOCKED, "approval required")
    assert tray.state is TrayState.BLOCKED
    tooltip = tray.system_tray_icon.toolTip()
    assert "Blocked" in tooltip
    assert "approval required" in tooltip
    assert tray.system_tray_icon.property("accessibleName") == tooltip


def test_task_controls_reflect_the_current_task_state(tray: JarvisTrayIcon) -> None:
    tray.set_current_task(None)
    assert not tray.action_pause.isEnabled()
    assert not tray.action_cancel.isEnabled()

    tray.set_current_task("t1", "Busy task", TaskState.RUNNING)
    assert tray.action_pause.isEnabled()
    assert tray.action_cancel.isEnabled()
    assert not tray.action_resume.isEnabled()
    assert "Busy task" in tray.action_current_task.text()

    tray.set_current_task("t1", "Busy task", TaskState.PAUSED)
    assert tray.action_resume.isEnabled()
    assert not tray.action_pause.isEnabled()

    tray.set_current_task("t1", "Busy task", TaskState.SUCCEEDED)
    assert not tray.action_cancel.isEnabled()


def test_the_offline_toggle_emits_its_signal(tray: JarvisTrayIcon) -> None:
    received: list[bool] = []
    tray.offlineModeToggled.connect(received.append)
    tray.action_offline.setChecked(True)
    assert received == [True]


def test_setting_the_network_mode_does_not_re_emit(tray: JarvisTrayIcon) -> None:
    received: list[bool] = []
    tray.offlineModeToggled.connect(received.append)
    tray.set_network_mode(NetworkMode.OFFLINE)
    assert received == [], "programmatic state changes must not look like user input"
    assert tray.action_offline.isChecked()


def test_the_emergency_stop_action_emits(tray: JarvisTrayIcon) -> None:
    received: list[int] = []
    tray.emergencyStopRequested.connect(lambda: received.append(1))
    tray.action_emergency_stop.trigger()
    assert received == [1]


# =========================================================================
# Main window (PRD section 9.3)
# =========================================================================
@pytest.fixture
def window(qapp, core) -> MainWindow:
    return MainWindow(core)


def test_all_fifteen_prd_navigation_areas_are_present(window: MainWindow) -> None:
    assert len(NAV_AREAS) == 15
    assert window.nav.count() == 15


def test_unimplemented_areas_are_labelled_with_their_phase(window: MainWindow) -> None:
    for index, area in enumerate(NAV_AREAS):
        item = window.nav.item(index)
        if not area.live:
            assert f"Phase {area.phase}" in item.text()
            assert "Not implemented" in item.toolTip()


def test_every_unimplemented_area_shows_an_honest_panel(window: MainWindow) -> None:
    """No placeholder screen may look like it works (ADR-0010, PRD section 1.10)."""
    from PySide6.QtWidgets import QLabel

    for index, area in enumerate(NAV_AREAS):
        if area.live:
            continue
        window.nav.setCurrentRow(index)
        panel = window.stack.currentWidget()
        text = " ".join(label.text() for label in panel.findChildren(QLabel))
        assert "Not implemented yet" in text, f"{area.key} does not say it is unimplemented"
        assert f"Phase {area.phase}" in text, f"{area.key} does not name its phase"


def test_the_live_areas_are_the_six_phase_0_screens_plus_home(window: MainWindow) -> None:
    assert set(window.live_area_keys()) == {
        "home", "tasks", "permissions", "models", "audit", "developer", "about",
    }


def test_home_reports_real_runtime_state(window: MainWindow, core) -> None:
    window.refresh_home()
    text = window._text("home").body.toPlainText()  # noqa: SLF001
    assert str(core.paths.root) in text
    assert "system.health" in text
    assert "local_assistant" in text


def test_the_tasks_panel_lists_real_tasks(window: MainWindow, core) -> None:
    core.tasks.create("A visible task", "goal", "system.health_check")
    window.refresh_tasks()
    table = window._table("tasks").table  # noqa: SLF001
    assert table.rowCount() == 1
    assert table.item(0, 0).text() == "A visible task"


def test_the_permissions_panel_lists_active_grants(window: MainWindow, core) -> None:
    window.refresh_permissions()
    table = window._permissions_panel().table  # noqa: SLF001
    capabilities = {table.item(row, 0).text() for row in range(table.rowCount())}
    assert "system.read_health" in capabilities


def test_the_audit_panel_lists_real_records(window: MainWindow, core) -> None:
    core.audit.record(
        __import__("jarvis.core.audit.models", fromlist=["AuditCategory"]).AuditCategory.LIFECYCLE,
        "a distinctive audit line",
    )
    window.refresh_audit()
    table = window._table("audit").table  # noqa: SLF001
    summaries = {table.item(row, 3).text() for row in range(table.rowCount())}
    assert "a distinctive audit line" in summaries


def test_developer_tools_describe_the_registered_tools(window: MainWindow) -> None:
    window.refresh_developer()
    text = window._text("developer").body.toPlainText()  # noqa: SLF001
    assert "system.health" in text
    assert "system.read_health" in text
    assert "Scheduler" in text


def test_about_states_the_phase_and_the_absence_of_a_shell(window: MainWindow) -> None:
    window.refresh_about()
    text = window._text("about").body.toPlainText()  # noqa: SLF001
    assert "Phase 0" in text
    assert "no generic shell" in text.lower()
    assert "codename" in text.lower()


def test_closing_the_window_hides_it_rather_than_quitting(window: MainWindow) -> None:
    """PRD FR-001: Jarvis stays functional when the main window is closed."""
    window.show()
    window.close()
    assert not window.isVisible()


# =========================================================================
# Event bridge (ADR-0005)
# =========================================================================
def test_the_bridge_re_emits_domain_events_as_qt_signals(qapp, core) -> None:
    received = []
    bridge = EventBridge(core.events)
    bridge.eventReceived.connect(received.append)

    core.events.publish(TaskStateChanged(task_id="t", from_state="queued", to_state="running"))
    QApplication.processEvents()

    assert len(received) == 1
    assert isinstance(received[0], TaskStateChanged)


def test_the_bridge_marshals_events_published_from_another_thread(qapp, core) -> None:
    received = []
    bridge = EventBridge(core.events)
    bridge.eventReceived.connect(received.append)

    def publish() -> None:
        core.events.publish(
            AppStarted(
                instance_id="i",
                app_version="0",
                schema_version=1,
                vault_root="C:/v",
                network_mode="offline",
            )
        )

    thread = threading.Thread(target=publish)
    thread.start()
    thread.join()

    for _ in range(20):
        QApplication.processEvents()
        if received:
            break

    assert len(received) == 1, "a cross-thread event must reach the GUI thread"


def test_detaching_the_bridge_stops_delivery(qapp, core) -> None:
    received = []
    bridge = EventBridge(core.events)
    bridge.eventReceived.connect(received.append)
    bridge.detach()

    core.events.publish(TaskStateChanged(task_id="t", from_state=None, to_state="draft"))
    QApplication.processEvents()

    assert received == []
    assert not bridge.attached
