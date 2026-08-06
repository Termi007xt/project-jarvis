"""Phase 0 exit criteria and hard constraints.

One test (or small group) per criterion in PRD section 21 "Phase 0", plus the
build constraints this project was given. This file is the checklist: if it is
green, Phase 0 is done in the sense the PRD means.
"""

from __future__ import annotations

import ast
import threading
import time
from pathlib import Path

import pytest

from jarvis.config.schema import AppConfig, NetworkMode
from jarvis.config.store import ConfigStore
from jarvis.core.audit.models import AuditCategory
from jarvis.core.events.bus import EventBus
from jarvis.core.events.types import Event
from jarvis.core.permissions.models import (
    Decision,
    GrantScope,
    PermissionRequest,
    RiskLevel,
)
from jarvis.core.tools.contract import ToolSpec
from jarvis.core.tools.prohibited import check_tool_id
from jarvis.runtime.core import JarvisCore
from jarvis.runtime.single_instance import AlreadyRunningError, SingleInstanceGuard
from jarvis.storage.migrations import SCHEMA_VERSION
from jarvis.tasks.states import TaskState


def wait_for(predicate, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


# =========================================================================
# Exit criterion 1: the application opens and sits in the tray
# =========================================================================
@pytest.mark.ui
def test_exit_1_the_application_opens_and_provides_a_tray_presence(qapp, core) -> None:
    from jarvis.ui.app import JarvisApplication

    application = JarvisApplication(core, qapp)
    try:
        assert application.tray is not None
        assert application.window is not None
        assert application.tray.menu.actions(), "the tray must offer a menu"
        # PRD FR-001: closing the window leaves Jarvis running.
        application.window.show()
        application.window.close()
        assert not application.window.isVisible()
        assert core.started
    finally:
        application.bridge.detach()
        application._refresh_timer.stop()  # noqa: SLF001


@pytest.mark.ui
def test_exit_1_the_tray_communicates_state_without_relying_on_colour(qapp) -> None:
    """PRD section 9.1 and NFR-033."""
    from jarvis.ui.icons import TrayState
    from jarvis.ui.tray import JarvisTrayIcon

    tray = JarvisTrayIcon()
    for state in TrayState:
        tray.set_state(state, "detail")
        assert state.label.split(",")[0].lower() in tray.system_tray_icon.toolTip().lower()
        assert tray.system_tray_icon.property("accessibleName")


# =========================================================================
# Exit criterion 2: settings persist
# =========================================================================
def test_exit_2_settings_persist_across_a_full_restart(vault) -> None:
    def build() -> JarvisCore:
        return JarvisCore(
            vault,
            config_store=ConfigStore(vault, env={}),
            enforce_single_instance=False,
        )

    first = build().start()
    first.set_setting("ui.start_minimised_to_tray", False)
    first.set_setting("logging.level", "WARNING")
    first.shutdown("test")

    second = build().start()
    try:
        assert second.config.ui.start_minimised_to_tray is False
        assert second.config.logging.level == "WARNING"
    finally:
        second.shutdown("test")


def test_exit_2_only_overrides_are_persisted(core: JarvisCore) -> None:
    core.set_setting("logging.level", "DEBUG")
    assert core.config_store.user_overrides() == {"logging": {"level": "DEBUG"}}


# =========================================================================
# Exit criterion 3: single-instance enforcement works
# =========================================================================
def test_exit_3_a_second_instance_is_refused(vault) -> None:
    """PRD FR-005."""
    lock = vault.runtime_dir / "exit3.lock"
    first = JarvisCore(
        vault,
        config_store=ConfigStore(vault, env={}),
        single_instance=SingleInstanceGuard(lock_file=lock, force_lock_file=True),
        enforce_single_instance=True,
    ).start()
    try:
        with pytest.raises(AlreadyRunningError):
            JarvisCore(
                vault,
                config_store=ConfigStore(vault, env={}),
                single_instance=SingleInstanceGuard(lock_file=lock, force_lock_file=True),
                enforce_single_instance=True,
            ).start()
    finally:
        first.shutdown("test")


# =========================================================================
# Exit criterion 4: audit events are written
# =========================================================================
def test_exit_4_audit_events_are_written_to_disk_and_indexed(core: JarvisCore) -> None:
    task_id = core.run_health_check_task()
    assert wait_for(lambda: core.tasks.require(task_id).is_terminal)

    assert core.paths.audit_log_path.is_file()

    # The SQLite index is read *first*, and the JSONL record of truth second.
    # Each event is appended to JSONL before it is indexed, so in that order
    # the index can only ever be a subset — whereas comparing counts the other
    # way round races the health worker, which keeps writing while the test
    # reads. The subset relation is the real invariant; equal counts were only
    # ever an accident of timing.
    indexed = {
        str(row["audit_id"])
        for row in core.database.query_all("SELECT audit_id FROM audit_event")
    }
    records = core.audit.read_all()
    assert len(records) > 0
    assert indexed, "the SQLite search index must be populated"

    categories = {record["category"] for record in records}
    assert {"lifecycle", "permission", "tool", "task"} <= categories

    on_disk = {str(record["audit_id"]) for record in records}
    assert indexed <= on_disk, "every indexed event must exist in the record of truth"


def test_exit_4_every_audit_record_carries_the_prd_11_5_fields(core: JarvisCore) -> None:
    core.audit.record(
        AuditCategory.TOOL,
        "example",
        task_id="t",
        conversation_id="c",
        tool_id="system.health",
        permission_decision="allow",
        parameters={"a": 1},
        pre_state={"b": 2},
        result="succeeded",
        verification="verified",
        evidence_ref="ref",
    )
    record = core.audit.read_all()[-1]
    for field in (
        "occurred_at", "task_id", "conversation_id", "tool_id", "parameters",
        "permission_decision", "pre_state", "result", "verification", "error",
        "evidence_ref",
    ):
        assert field in record


def test_exit_4_the_audit_log_is_searchable_and_exportable(core: JarvisCore, tmp_path) -> None:
    core.audit.record(AuditCategory.SECURITY, "searchable line")
    assert core.audit.query(category=AuditCategory.SECURITY)
    destination = core.audit.export(tmp_path / "audit-export.jsonl")
    assert "searchable line" in destination.read_text(encoding="utf-8")


# =========================================================================
# Exit criterion 5: permission decisions are testable
# =========================================================================
def test_exit_5_permission_decisions_are_deterministic_and_inspectable(core) -> None:
    low = core.permissions.evaluate(PermissionRequest(capability_id="notify.show"))
    medium = core.permissions.evaluate(PermissionRequest(capability_id="clipboard.read"))
    high = core.permissions.evaluate(PermissionRequest(capability_id="app.force_close"))
    prohibited = core.permissions.evaluate(
        PermissionRequest(capability_id="prohibited.generic_shell")
    )

    assert low.decision is Decision.ASK and low.risk is RiskLevel.LOW
    assert medium.decision is Decision.ASK and medium.risk is RiskLevel.MEDIUM
    assert high.decision is Decision.ASK and high.requires_user_approval
    assert prohibited.decision is Decision.DENY and not prohibited.requires_user_approval

    for evaluation in (low, medium, high, prohibited):
        assert evaluation.reason, "every decision must explain itself"


def test_exit_5_high_risk_never_gets_a_standing_allow(core) -> None:
    """PRD section 9.9."""
    from jarvis.core.permissions.models import PermissionError as JarvisPermissionError

    with pytest.raises(JarvisPermissionError):
        core.permissions.grant(
            "fs.delete_or_overwrite", Decision.ALLOW, GrantScope.ALWAYS, created_by="user"
        )


# =========================================================================
# Exit criterion 6: no generic shell exists anywhere in the runtime
# =========================================================================
def test_exit_6_no_prohibited_tool_can_be_registered(core) -> None:
    for name in ("run_shell", "execute_code", "run_powershell", "control_computer"):
        assert not check_tool_id(name)


def test_exit_6_the_registered_tool_set_is_narrow(core: JarvisCore) -> None:
    """The tool set stays small and low risk.

    Phase 0 registered exactly one tool. Phase 1 adds the five PRD section 21
    names plus ``notify.show``, which only a shell can back. The invariant that
    still has to hold is not the count but the shape: everything registered is
    **low risk**, and nothing has appeared that no phase asked for.
    """
    specs = core.registry.specs()
    registered = {spec.tool_id for spec in specs}

    expected = {
        "system.health",      # Phase 0
        "app.open",           # Phase 1, PRD section 21
        "web.open_url",
        # Added after acceptance testing: asked to search, the model built its
        # own URL and produced a malformed one that Google answered with 400.
        # A narrow tool that takes words and does the encoding removes the
        # whole class of error. It widens nothing — same capability, same
        # browser, same scheme restriction as web.open_url.
        "web.search",
        "media.control",
        "device.volume",
        "voice.speak",
        # Phase 2, PRD section 21's exit criterion: "search RTX 5070 on YouTube
        # and play the second video" is two utterances, so it is two tools.
        # `youtube.play` takes a *position*, never a title — the injection
        # defence written into a signature rather than into a rule.
        "youtube.search",
        "youtube.play",
        # Added 2026-08-05 (ADR-0032). Brave cannot be given an automation port
        # while it is running, so a browser Jarvis had opened itself made its
        # own next step impossible — and the only way out was the owner quitting
        # Brave by hand, which they did three times in four minutes. Its own
        # tool and its own capability rather than folded into `youtube.search`:
        # approving a search is not approving the loss of someone's windows.
        "browser.restart",
        # Phase 2 stage 4 (P2-WIN-08, P2-WIN-09). Two tools, not one, because
        # reading which windows are open and taking the foreground away from
        # what the owner is doing are different risks — `window.list` is low and
        # holds no lock, `window.arrange` is medium and owns the desktop first.
        # `window.arrange` takes a position from the listing and has no title
        # parameter at all, so a window cannot retarget an action by renaming
        # itself.
        "window.list",
        "window.arrange",
        # Phase 2 stage 4 (P2-APP-01, P2-APP-02). Two tools, and the split is
        # the whole control: `app.close` asks, the way clicking the X asks, and
        # stops when the application raises a save prompt. `app.force_close`
        # discards that work, and reaching it has to be a decision a person
        # makes — which a separate tool requires and a `force=True` parameter
        # would not.
        "app.close",
        "app.force_close",
    }
    assert registered == expected, (
        "the registered tool set has drifted from what the phases declare"
    )

    # The invariant is no longer "everything is low risk" — Phase 2's browser
    # automation drives a profile that may hold live logins, and PRD section
    # 11.1 classes that as medium, so pretending otherwise would be the
    # dishonesty this test exists to prevent.
    #
    # Phase 2 stage 4 added the first HIGH tool, `app.force_close` (FR-067,
    # AT-005). It is named here one at a time rather than the check being
    # relaxed to "high is allowed now": deletion, elevation, installing software
    # and sending messages are all still unbuilt, and the value of this test is
    # entirely in none of them arriving unannounced.
    high_risk_by_design = {"app.force_close"}
    for spec in specs:
        if spec.tool_id in high_risk_by_design:
            assert spec.risk is RiskLevel.HIGH, (
                f"{spec.tool_id} is listed as high-risk by design but declares "
                f"{spec.risk.value}; losing unsaved work is not a medium-risk act"
            )
            continue
        assert spec.risk in (RiskLevel.LOW, RiskLevel.MEDIUM), (
            f"{spec.tool_id} is {spec.risk.value}; no phase has asked for a "
            "high-risk or prohibited tool beyond "
            f"{sorted(high_risk_by_design)}"
        )


def test_exit_6_a_state_changing_tool_must_declare_how_it_verifies(
    core: JarvisCore,
) -> None:
    """PRD FR-048: succeeded requires verification, so it must be declared."""
    for spec in core.registry.specs():
        if spec.changes_state:
            assert spec.verification, f"{spec.tool_id} changes state but declares no check"


def test_exit_6_the_planner_is_offered_only_registered_tools(core: JarvisCore) -> None:
    """PRD section 13.4: free-form text can never be executed."""
    described = core.invoker.describe_tools()
    assert {entry["name"] for entry in described} == set(core.registry.tool_ids())


# =========================================================================
# Hard constraint: no computer-control features in Phase 0
# =========================================================================
def test_no_capability_requiring_input_screen_or_filesystem_access_is_wired(
    core: JarvisCore,
) -> None:
    # `browser.automate_logged_in` left this set in Phase 2, when the browser
    # tools it names were actually built (ADR-0019, ADR-0031). Everything else
    # is still unbuilt, and the point of keeping the list rather than deleting
    # the test is that none of these may arrive unannounced — `input.automate`
    # in particular, because Phase 2 stage 2 built the *permission* to move the
    # pointer and no tool has been given it yet.
    still_unbuilt = {
        "input.automate",
        "screen.capture",
        "clipboard.read",
        "clipboard.write",
        "fs.read_approved",
        "fs.write_approved",
        "fs.delete_or_overwrite",
        # `app.force_close` left this set in Phase 2 stage 4, when P2-APP-02
        # built it (FR-067, AT-005). It is the first high-risk tool in the
        # product, and it earns that by being the only way to lose unsaved work
        # on purpose: fresh confirmation every time, no standing grant ever, and
        # deliberately a separate tool from `app.close` so that reaching it is
        # something a person decides rather than a parameter a model sets.
        "system.elevate",
    }
    for spec in core.registry.specs():
        wired = set(spec.required_capabilities) & still_unbuilt
        assert not wired, (
            f"{spec.tool_id} requires {sorted(wired)}, which no completed phase "
            "has built. If a phase has now built it, say so here rather than "
            "removing the check."
        )


def test_no_screenshot_or_input_automation_module_exists(repo_root: Path) -> None:
    """Screenshot-based computer control is still out of scope.

    Phase 1 legitimately adds ``jarvis.audio``, so the "no audio package"
    assertion this test carried through Phase 0 has been replaced by the
    constraint it was really protecting: no heavy or computer-control library
    may be imported at module scope. That keeps the engine importable on Linux
    with no audio stack installed, which is what makes the CI matrix meaningful
    (ARCHITECTURE section 11). See ``tests/security/test_lazy_audio_imports.py``
    for the Phase 1 statement of the same rule.
    """
    package = repo_root / "src" / "jarvis"
    assert not (package / "automation").exists(), "automation lands in Phase 2"

    banned_imports = {"mss", "pyautogui", "pywinauto", "playwright", "PIL", "cv2"}
    for path in package.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        # Module scope only, deliberately not `ast.walk` — same reasoning, and
        # the same implementation, as
        # `tests/security/test_lazy_audio_imports.py`. Phase 2 legitimately uses
        # pywinauto and playwright behind the `automation` extra, exactly as
        # Phase 1 uses the voice stack behind the `voice` extra, and a lazy
        # import inside a function is what makes that work. Scanning the whole
        # tree would have banned the sanctioned pattern along with the
        # unsanctioned one, which is stricter than this test's own stated rule.
        scoped: list[ast.AST] = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                scoped.append(node)
            elif isinstance(node, ast.If):
                # A module-level `if` (a TYPE_CHECKING guard, say) still runs.
                scoped.extend(ast.walk(node))

        for node in scoped:
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            assert not (set(names) & banned_imports), (
                f"{path.name} imports a computer-control library at module "
                f"scope: {set(names) & banned_imports}. Import it inside the "
                "function that needs it, so the engine still imports on Linux "
                "with nothing installed (ARCHITECTURE §11)."
            )


def test_the_computer_control_scanner_still_catches_a_violation() -> None:
    """A scan that was just narrowed must be shown to still detect something.

    The check above was widened from "any import anywhere" to "any import at
    module scope" when Phase 2 gave pywinauto a legitimate lazy use. A narrowing
    that goes too far produces a test that passes because it inspects nothing,
    which is the failure mode this project keeps meeting — so this proves the
    scanner still bites, and that the sanctioned pattern still passes.
    """
    banned = {"mss", "pyautogui", "pywinauto", "playwright", "PIL", "cv2"}

    def module_scope_hits(source: str) -> set[str]:
        tree = ast.parse(source)
        scoped: list[ast.AST] = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                scoped.append(node)
            elif isinstance(node, ast.If):
                scoped.extend(ast.walk(node))
        found: set[str] = set()
        for node in scoped:
            if isinstance(node, ast.Import):
                found |= {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module.split(".")[0])
        return found & banned

    assert module_scope_hits("import pywinauto\n") == {"pywinauto"}
    assert module_scope_hits("from playwright.sync_api import sync_playwright\n") == {"playwright"}
    assert module_scope_hits("if TYPE_CHECKING:\n    import pywinauto\n") == {"pywinauto"}

    # The sanctioned pattern: lazy, inside the function that needs it.
    assert module_scope_hits("def go():\n    import pywinauto\n    return pywinauto\n") == set()


# =========================================================================
# Hard constraint: no silent memory creation, no self-modification
# =========================================================================
def test_no_memory_subsystem_writes_anything_in_phase_0(core: JarvisCore) -> None:
    """PRD section 4.4: nothing may silently become permanent memory."""
    tables = {
        row["name"]
        for row in core.database.query_all("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert "memory" not in tables, "the memory subsystem arrives in Phase 3, with approval flow"


def test_the_runtime_never_writes_to_its_own_source(core: JarvisCore, repo_root: Path) -> None:
    """No autonomous self-modification: every write path targets the vault."""
    for directory in core.paths.all_directories():
        assert repo_root / "src" not in directory.parents
        assert directory != repo_root / "src"


# =========================================================================
# Hard constraint: typed schemas, structured calls, locks, audit, tasks
# =========================================================================
def test_configuration_is_typed_and_rejects_unknown_keys(config: AppConfig) -> None:
    assert isinstance(config, AppConfig)
    assert config.model_config["extra"] == "forbid"
    assert config.model_config["frozen"] is True


def test_events_are_typed_and_immutable() -> None:
    assert Event.model_config["frozen"] is True
    assert Event.model_config["extra"] == "forbid"


def test_every_tool_declares_the_full_prd_13_2_contract(core: JarvisCore) -> None:
    required = {
        "tool_id", "version", "description", "input_model", "output_model", "risk",
        "required_capabilities", "resource_locks", "timeout_seconds", "retry_policy",
        "changes_state", "verification", "redaction_keys", "supported_applications",
        "failure_codes", "reversible", "rollback",
    }
    assert required <= set(ToolSpec.model_fields)
    for spec in core.registry.specs():
        assert spec.required_capabilities
        assert spec.failure_codes
        assert spec.timeout_seconds > 0


def test_resource_locks_exist_and_are_exclusive(core: JarvisCore) -> None:
    """PRD FR-124."""
    assert core.locks.acquire("task-a", ["foreground_desktop"]) is not None
    assert core.locks.acquire("task-b", ["foreground_desktop"]) is None


def test_the_task_state_machine_is_persistent(core: JarvisCore, vault) -> None:
    # Stop the scheduler first, so the task stays queued instead of being
    # dispatched while the test is asserting on it.
    core.scheduler.stop()
    task = core.tasks.create("Durable", "goal", "system.health_check")
    core.tasks.transition(task.task_id, TaskState.QUEUED)
    core.shutdown("test")

    reopened = JarvisCore(
        vault, config_store=ConfigStore(vault, env={}), enforce_single_instance=False
    ).start()
    try:
        assert reopened.tasks.require(task.task_id).state is TaskState.QUEUED
        assert reopened.tasks.transitions(task.task_id)
    finally:
        reopened.shutdown("test")


# =========================================================================
# Hard constraint: work happens off the UI thread
# =========================================================================
def test_the_scheduler_and_workers_run_on_their_own_threads(core: JarvisCore) -> None:
    """PRD NFR-003."""
    main_thread = threading.current_thread()
    observed: list[str] = []

    class _ThreadRecordingRunner:
        runner_id = "test.thread_probe"

        def run(self, context):
            from jarvis.tasks.runner import TaskOutcome

            observed.append(threading.current_thread().name)
            return TaskOutcome(state=TaskState.SUCCEEDED, summary="done")

    core.scheduler.register_runner(_ThreadRecordingRunner())
    task = core.tasks.create("Probe", "goal", "test.thread_probe")
    core.scheduler.submit(task)

    assert wait_for(lambda: core.tasks.require(task.task_id).is_terminal)
    assert observed, "the runner never ran"
    assert observed[0] != main_thread.name
    assert observed[0].startswith("jarvis-task")


def test_the_health_check_runs_on_a_worker_thread(core: JarvisCore) -> None:
    assert "health" in core.workers.running_names()


# =========================================================================
# Deliverables present
# =========================================================================
@pytest.mark.parametrize(
    "relative",
    [
        "ARCHITECTURE.md",
        "SECURITY.md",
        "THREAT_MODEL.md",
        "DATA_MODEL.md",
        "CHANGELOG.md",
        "README.md",
        "docs/BACKLOG.md",
        "pyproject.toml",
        "config/defaults.yaml",
        ".github/workflows/ci.yml",
    ],
)
def test_required_documents_and_config_exist(repo_root: Path, relative: str) -> None:
    path = repo_root / relative
    assert path.is_file(), f"{relative} is missing"
    assert path.stat().st_size > 0, f"{relative} is empty"


def test_an_adr_exists_for_every_prd_open_decision(repo_root: Path) -> None:
    """PRD section 25 lists sixteen open decisions."""
    adrs = sorted((repo_root / "docs" / "decisions").glob("ADR-*.md"))
    assert len(adrs) >= 26, f"expected at least 26 ADRs, found {len(adrs)}"
    numbers = {int(path.name.split("-")[1]) for path in adrs}
    assert set(range(1, 27)) <= numbers, f"missing ADR numbers: {set(range(1, 27)) - numbers}"


def test_the_schema_version_is_recorded(core: JarvisCore) -> None:
    assert core.database.user_version() == SCHEMA_VERSION
    assert core.status().schema_version == SCHEMA_VERSION


def test_the_cli_check_command_reports_status(vault) -> None:
    from jarvis.main import main

    exit_code = main(
        ["--check", "--data-dir", str(vault.root), "--allow-multiple-instances"]
    )
    assert exit_code == 0


def test_check_stays_successful_when_the_model_runtime_is_unreachable(
    vault, monkeypatch
) -> None:
    """An honest report of an unreachable runtime is a successful self-check.

    Settled 2026-08-02 (PROJECT_STATE decision 7): --check keeps exit 0, and
    callers needing the stronger statement pass --require-healthy.
    """
    from jarvis.main import main

    monkeypatch.setenv("JARVIS__LLM__OLLAMA__BASE_URL", "http://127.0.0.1:1")
    assert main(["--check", "--data-dir", str(vault.root), "--allow-multiple-instances"]) == 0


def test_require_healthy_makes_an_unreachable_runtime_a_failure(
    vault, monkeypatch, capsys
) -> None:
    from jarvis.main import main

    monkeypatch.setenv("JARVIS__LLM__OLLAMA__BASE_URL", "http://127.0.0.1:1")
    exit_code = main(
        [
            "--check",
            "--require-healthy",
            "--data-dir",
            str(vault.root),
            "--allow-multiple-instances",
        ]
    )
    assert exit_code == 1
    assert "--require-healthy" in capsys.readouterr().err


def test_check_reports_the_voice_stack_and_secret_store(vault, capsys) -> None:
    """Phase 1 state must be visible from the headless self-check."""
    from jarvis.main import main

    main(["--check", "--data-dir", str(vault.root), "--allow-multiple-instances"])
    output = capsys.readouterr().out
    assert "voice stack" in output
    assert "secret store" in output


def test_offline_mode_is_reachable_from_configuration(core: JarvisCore) -> None:
    core.set_network_mode(NetworkMode.OFFLINE)
    assert core.config.network.mode is NetworkMode.OFFLINE
    assert core.refresh_health().skipped
