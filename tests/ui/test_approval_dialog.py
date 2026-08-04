"""The approval surface (PRD section 11.2, ADR-0027).

Runs offscreen. What is asserted here is the behaviour ADR-0027 made
load-bearing: the panel renders the full PRD 11.2 field set, it does not steal
focus, the buttons it draws match the offered scopes exactly, and the tray plus
the window make a non-modal request impossible to miss.
"""

from __future__ import annotations

import threading
import time
from typing import Iterator

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QPushButton  # noqa: E402

from jarvis.core.permissions.catalogue import CAPABILITIES  # noqa: E402
from jarvis.core.permissions.models import Decision, GrantScope, RiskLevel  # noqa: E402
from jarvis.core.tools.approvals import ApprovalQueue  # noqa: E402
from jarvis.core.tools.ports import (  # noqa: E402
    ApprovalRequest,
    denial_options_for,
    offerable_scopes_for,
)
from jarvis.ui.approval import ApprovalController, ApprovalPanel  # noqa: E402

pytestmark = pytest.mark.ui


def make_request(
    *,
    risk: RiskLevel = RiskLevel.MEDIUM,
    capability_id: str = "fs.read_approved",
    target: str | None = "C:/notes",
    task_id: str | None = None,
    reversible: bool = True,
) -> ApprovalRequest:
    capability = CAPABILITIES.get(capability_id)
    return ApprovalRequest(
        capability_id=capability_id,
        capability_title=capability.title if capability else capability_id,
        risk=risk,
        tool_id="test.tool",
        action_summary="Read the files in your notes folder",
        initiating_utterance="find my meeting notes",
        target=target,
        parameters={"path": "C:/notes"},
        scope_description="fs.read_approved for C:/notes",
        reversible=reversible,
        task_id=task_id,
        offerable_scopes=offerable_scopes_for(risk),
        denial_options=denial_options_for(capability, target),
    )


@pytest.fixture
def queue(audit, events) -> ApprovalQueue:
    q = ApprovalQueue(audit=audit, event_bus=events, timeout_seconds=5.0)
    q.set_interactive(True)
    return q


@pytest.fixture
def panel(qapp) -> Iterator[ApprovalPanel]:
    widget = ApprovalPanel()
    yield widget
    widget.close()
    widget.deleteLater()


def _pending(queue: ApprovalQueue, request: ApprovalRequest):
    """Queue a request and return *its* pending entry, not merely the oldest."""
    thread = threading.Thread(target=lambda: queue.request_approval(request), daemon=True)
    thread.start()
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        for entry in queue.pending():
            if entry.approval_id == request.approval_id:
                return entry, thread
        time.sleep(0.005)
    raise AssertionError("the request never became pending")


def _buttons(panel: ApprovalPanel) -> list[str]:
    return [b.text() for b in panel.findChildren(QPushButton)]


# -- PRD 11.2 field set -----------------------------------------------------
def test_the_panel_shows_every_prd_11_2_field(panel: ApprovalPanel, queue) -> None:
    pending, _ = _pending(queue, make_request())
    panel.show_request(pending)

    text = panel.detail.text()
    assert "Read the files in your notes folder" in panel.heading.text()  # requested action
    assert "find my meeting notes" in text  # initiating user request
    assert "test.tool" in text  # tool
    assert "C:/notes" in text  # application and target
    assert "path=" in text  # data involved
    assert "fs.read_approved for C:/notes" in text  # exact scope
    assert "medium risk" in panel.risk_label.text().lower()  # risk category
    assert "reversible" in panel.risk_label.text()  # whether it is reversible


def test_an_irreversible_action_says_so_plainly(panel: ApprovalPanel, queue) -> None:
    pending, _ = _pending(
        queue,
        make_request(risk=RiskLevel.HIGH, capability_id="fs.delete_or_overwrite",
                     reversible=False),
    )
    panel.show_request(pending)
    assert "cannot be undone" in panel.detail.text()
    assert "not reversible" in panel.risk_label.text()


def test_the_countdown_states_what_silence_means(panel: ApprovalPanel, queue) -> None:
    pending, _ = _pending(queue, make_request())
    panel.show_request(pending)
    assert "denied" in panel.countdown.text()


# -- the buttons match the offered scopes -----------------------------------
def test_a_medium_risk_request_offers_once_and_this_task(panel: ApprovalPanel, queue) -> None:
    pending, _ = _pending(queue, make_request())
    panel.show_request(pending)
    labels = _buttons(panel)
    assert "Allow once" in labels
    assert "Allow for this task" in labels
    assert "Deny" in labels
    assert "Allow always" not in labels


def test_a_high_risk_request_offers_only_allow_once_and_deny(
    panel: ApprovalPanel, queue
) -> None:
    pending, _ = _pending(
        queue, make_request(risk=RiskLevel.HIGH, capability_id="fs.delete_or_overwrite")
    )
    panel.show_request(pending)
    labels = _buttons(panel)
    assert "Allow once" in labels
    assert "Deny" in labels
    assert "Allow for this task" not in labels
    assert "Allow always" not in labels


def test_a_scoped_request_offers_to_remember_the_denial(panel: ApprovalPanel, queue) -> None:
    pending, _ = _pending(queue, make_request())
    panel.show_request(pending)
    assert any("Don't ask again" in label for label in _buttons(panel))


def test_stop_task_appears_only_when_there_is_a_task(panel: ApprovalPanel, queue) -> None:
    pending, _ = _pending(queue, make_request(task_id="task-1"))
    panel.show_request(pending)
    assert any("stop the task" in label for label in _buttons(panel))

    other, _ = _pending(queue, make_request())
    panel.show_request(other)
    assert not any("stop the task" in label for label in _buttons(panel))


# -- non-modality (the whole reason for ADR-0027) ---------------------------
def test_the_panel_does_not_steal_focus(panel: ApprovalPanel) -> None:
    """A modal prompt would break the automation it is asking about."""
    assert panel.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    assert not panel.isModal()


def test_the_panel_is_a_tool_window_that_stays_on_top(panel: ApprovalPanel) -> None:
    flags = panel.windowFlags()
    assert flags & Qt.WindowType.WindowStaysOnTopHint
    assert flags & Qt.WindowType.Tool


# -- answering through the controller ---------------------------------------
def test_clicking_allow_once_resolves_the_request(qapp, queue) -> None:
    controller = ApprovalController(queue)
    request = make_request()
    pending, thread = _pending(queue, request)
    controller.refresh()

    controller.panel._answer(Decision.ALLOW, GrantScope.ONCE, None)  # noqa: SLF001
    thread.join(timeout=2)

    assert not queue.pending()
    controller.panel.close()


def test_a_forged_scope_from_the_dialog_is_refused_not_honoured(qapp, queue) -> None:
    """The queue is the authority; the panel cannot widen a high-risk grant."""
    controller = ApprovalController(queue)
    request = make_request(risk=RiskLevel.HIGH, capability_id="fs.delete_or_overwrite")
    _pending(queue, request)
    controller.refresh()

    # Simulate a defective dialog offering a scope the request never allowed.
    controller.panel._answer(Decision.ALLOW, GrantScope.ALWAYS, None)  # noqa: SLF001

    assert queue.pending(), "the request must still be waiting, not wrongly allowed"
    queue.deny_all("test teardown")
    controller.panel.close()


def test_focusing_the_panel_reports_whether_anything_was_waiting(qapp, queue) -> None:
    controller = ApprovalController(queue)
    assert controller.focus_panel() is False

    _pending(queue, make_request())
    assert controller.focus_panel() is True

    queue.deny_all("test teardown")
    controller.panel.close()


# -- the tray and window carry the visibility a modal dialog would have -----
def test_the_tray_offers_a_keyboard_route_only_when_something_waits(qapp) -> None:
    from jarvis.ui.tray import JarvisTrayIcon

    tray = JarvisTrayIcon()
    assert not tray.action_review_approval.isEnabled()

    tray.set_pending_approvals(1)
    assert tray.action_review_approval.isEnabled()
    assert "denied" in tray.action_review_approval.toolTip()

    tray.set_pending_approvals(0)
    assert not tray.action_review_approval.isEnabled()


def test_the_window_lists_a_pending_request_with_working_controls(qapp, core, queue) -> None:
    from jarvis.ui.main_window import MainWindow

    window = MainWindow(core)
    answered: list[tuple[str, bool]] = []
    window.approvalAnswered.connect(lambda i, a: answered.append((i, a)))

    pending, _ = _pending(queue, make_request())
    window.set_pending_approvals((pending,))

    panel = window._permissions_panel()  # noqa: SLF001
    assert panel.pending_list.count() == 1
    assert panel.allow_button.isEnabled()
    assert panel.selected_approval_id() == pending.approval_id

    panel._answer(False)  # noqa: SLF001
    assert answered == [(pending.approval_id, False)]

    queue.deny_all("test teardown")
    window.close()


def test_the_window_says_plainly_when_nothing_is_waiting(qapp, core) -> None:
    from jarvis.ui.main_window import MainWindow

    window = MainWindow(core)
    window.set_pending_approvals(())
    panel = window._permissions_panel()  # noqa: SLF001
    assert "Nothing is waiting" in panel.pending_heading.text()
    assert not panel.allow_button.isEnabled()
    window.close()
