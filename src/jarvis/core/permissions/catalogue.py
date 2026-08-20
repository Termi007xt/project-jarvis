"""The capability catalogue — PRD section 11.1 expressed as data.

Risk classification lives here so it can be tested directly against the PRD
rather than being scattered through call sites. Changing a capability's risk
level requires an ADR (ARCHITECTURE.md section 14).

Capabilities are declared for all phases, not only Phase 0. Declaring a
capability does not implement it: a capability with no tool behind it can never
be exercised, and the permission engine denies unknown capabilities outright.
"""

from __future__ import annotations

from jarvis.core.permissions.models import Capability, RiskLevel

__all__ = ["CAPABILITIES", "capability", "capability_ids", "capabilities_by_risk"]


def _c(
    capability_id: str,
    title: str,
    risk: RiskLevel,
    description: str,
    phase: int,
    *,
    reversible: bool = True,
    scope_kind: str | None = None,
) -> Capability:
    return Capability(
        capability_id=capability_id,
        title=title,
        risk=risk,
        description=description,
        phase=phase,
        reversible=reversible,
        scope_kind=scope_kind,
    )


_LOW = RiskLevel.LOW
_MEDIUM = RiskLevel.MEDIUM
_HIGH = RiskLevel.HIGH
_PROHIBITED = RiskLevel.PROHIBITED


_ALL: tuple[Capability, ...] = (
    # -- Low risk (PRD 11.1). May support "always allow". -----------------
    _c("system.read_health", "Read system health", _LOW,
       "Check the local model runtime and data vault status.", 0),
    _c("system.read_audit_log", "Read own audit log", _LOW,
       "Read the application's own audit records.", 0),
    _c("conversation.answer_local", "Answer from the local model", _LOW,
       "Answer a question using the local model only.", 1),
    _c("voice.speak", "Speak a response", _LOW,
       "Produce spoken output through the configured voice.", 1),
    _c("app.open_approved", "Open an approved application", _LOW,
       "Launch an application already approved in the catalogue.", 1,
       scope_kind="application"),
    _c("web.open_approved_url", "Open an approved website", _LOW,
       "Open a URL in the dedicated browser profile.", 1, scope_kind="url_host"),
    _c("device.control_volume", "Control volume", _LOW,
       "Change the system output volume.", 1),
    _c("media.playback_control", "Play or pause media", _LOW,
       "Send play, pause, next, previous or stop to the system media controls.", 1),
    _c("window.read_active_title", "Read the active window title", _LOW,
       "Read the title of the currently focused window.", 2),
    _c("window.read_layout", "See which windows are open", _LOW,
       "List the open windows, where they are on screen and whether they are "
       "minimised or maximised. Reads only; moves nothing. Windows belonging to "
       "sensitive applications are listed without their titles.", 2),
    _c("notify.show", "Show a notification", _LOW,
       "Display a Windows toast notification.", 1),

    # -- Medium risk. Ask every time, per task, per app or per folder. ----
    _c("input.automate", "Mouse and keyboard automation", _MEDIUM,
       "Move the mouse or send keystrokes to another application.", 2,
       reversible=False),
    _c("screen.capture", "Capture the screen", _MEDIUM,
       "Capture a control, window, region or monitor.", 2),
    _c("clipboard.read", "Read the clipboard", _MEDIUM,
       "Read the current clipboard contents.", 3),
    _c("clipboard.write", "Write the clipboard", _MEDIUM,
       "Replace or append to the clipboard contents.", 3),
    _c("fs.read_approved", "Read files in an approved folder", _MEDIUM,
       "Read file contents inside an approved root scope.", 2, scope_kind="folder"),
    _c("fs.write_approved", "Create or modify files in an approved folder", _MEDIUM,
       "Create or modify files inside an approved root scope.", 2, scope_kind="folder"),
    _c("browser.automate_logged_in", "Browser automation in a logged-in session", _MEDIUM,
       "Drive the dedicated browser profile, which may hold live logins.", 2,
       reversible=False, scope_kind="url_host"),
    _c("browser.restart", "Close and reopen the browser", _MEDIUM,
       "Close the browser and start it again so it can be automated. Open tabs "
       "are restored, because the browser is asked to close rather than killed.",
       2, scope_kind="application"),
    _c("window.arrange", "Move and arrange windows", _MEDIUM,
       "Bring a window to the front, minimise, maximise, restore, move or "
       "resize it. Medium rather than low because activating a window takes the "
       "foreground away from whatever you were doing.", 2,
       scope_kind="application"),
    _c("app.close", "Close an application", _MEDIUM,
       "Ask an application to close, the way clicking its X does. It may "
       "refuse, and one that raises a save prompt is left alone for you to "
       "answer. Never forces (that is app.force_close).", 2,
       scope_kind="application"),
    _c("app.monitor", "Monitor an application", _MEDIUM,
       "Observe a named application's visible state.", 4, scope_kind="application"),
    _c("messages.copy_private", "Copy private messages", _MEDIUM,
       "Read messages from a scoped conversation for an approved purpose.", 4),
    _c("models.manage_local", "Install or remove local models", _MEDIUM,
       "Download or delete a local model.", 6),
    _c("download.non_executable", "Download a non-executable file", _MEDIUM,
       "Download a file that is not an executable, into an approved folder.", 2,
       scope_kind="folder"),
    _c("watcher.start", "Start a long-running watcher", _MEDIUM,
       "Create a bounded, visible watcher task.", 4),

    # -- High risk. Fresh confirmation required every time. ---------------
    _c("fs.delete_or_overwrite", "Delete or overwrite files", _HIGH,
       "Recycle, delete or overwrite an existing file.", 3,
       reversible=False, scope_kind="folder"),
    _c("download.executable", "Download or run an executable", _HIGH,
       "Retrieve or launch executable content.", 6, reversible=False),
    _c("software.install", "Install software", _HIGH,
       "Install an application on this computer.", 6, reversible=False),
    _c("app.force_close", "Force-close an application", _HIGH,
       "Terminate a process rather than closing it normally.", 2,
       reversible=False, scope_kind="application"),
    _c("messages.send_or_delete", "Send, edit or delete a message", _HIGH,
       "Send, edit or delete a message or email.", 4, reversible=False),
    _c("form.submit_binding", "Submit a form that creates an obligation", _HIGH,
       "Submit a form that commits the user to something.", 4, reversible=False),
    _c("content.publish", "Publish content", _HIGH,
       "Post or publish content to an external service.", 4, reversible=False),
    _c("finance.transact", "Make a purchase or financial action", _HIGH,
       "Any purchase, transfer or financial commitment.", 99, reversible=False),
    _c("settings.change_security", "Change account, security or privacy settings", _HIGH,
       "Alter security, account or privacy configuration.", 4, reversible=False),
    _c("device.access_camera", "Access the camera", _HIGH,
       "Capture from a camera device.", 99, reversible=False),
    _c("data.export_sensitive", "Export sensitive data", _HIGH,
       "Export data classified as sensitive out of the vault.", 3, reversible=False),
    _c("ide.approve_terminal_command", "Approve an IDE terminal command", _HIGH,
       "Approve a command an IDE agent wants to run.", 5, reversible=False),
    _c("system.elevate", "Elevate privileges", _HIGH,
       "Run a single scoped action with administrator rights.", 99, reversible=False),
    _c("settings.modify_system", "Modify system settings", _HIGH,
       "Change a Windows setting.", 4, reversible=False),

    # -- Prohibited in the initial product. Denied unconditionally. -------
    # These exist so that a request for one is *named and audited* rather than
    # silently falling through as "unknown capability".
    _c("prohibited.generic_shell", "Generic shell execution", _PROHIBITED,
       "Run an arbitrary shell, Command Prompt, PowerShell or WSL command.", 99,
       reversible=False),
    _c("prohibited.arbitrary_script", "Arbitrary script execution", _PROHIBITED,
       "Execute arbitrary code or a generated script.", 99, reversible=False),
    _c("prohibited.read_secrets", "Read passwords or private keys", _PROHIBITED,
       "Read passwords, private keys or password-manager content.", 99),
    _c("prohibited.disable_security", "Disable antivirus or security controls", _PROHIBITED,
       "Turn off antivirus, firewall, SmartScreen, UAC or encryption.", 99,
       reversible=False),
    _c("prohibited.extract_credentials", "Credential or session extraction", _PROHIBITED,
       "Extract cookies, tokens or session material from another application.", 99),
    _c("prohibited.captcha_bypass", "CAPTCHA bypass", _PROHIBITED,
       "Defeat a CAPTCHA or anti-bot control.", 99),
    _c("prohibited.stealth_recording", "Stealth recording", _PROHIBITED,
       "Record audio or screen without a visible indicator.", 99),
    _c("prohibited.surveil_other_users", "Surveillance of other users", _PROHIBITED,
       "Observe another Windows user's activity or files.", 99),
    _c("prohibited.permanent_admin", "Permanent administrator operation", _PROHIBITED,
       "Run the application persistently with administrator rights.", 99),
    _c("prohibited.autonomous_finance", "Autonomous financial transaction", _PROHIBITED,
       "Complete a financial transaction without fresh user confirmation.", 99,
       reversible=False),
    _c("prohibited.autonomous_legal", "Autonomous legal acceptance", _PROHIBITED,
       "Accept terms or a legal agreement on the user's behalf.", 99, reversible=False),
    _c("prohibited.hidden_remote_control", "Hidden remote control", _PROHIBITED,
       "Expose control of this computer to a remote party.", 99, reversible=False),
)


CAPABILITIES: dict[str, Capability] = {item.capability_id: item for item in _ALL}

if len(CAPABILITIES) != len(_ALL):  # pragma: no cover - guarded by a unit test too
    raise RuntimeError("duplicate capability_id in the catalogue")


def capability(capability_id: str) -> Capability | None:
    return CAPABILITIES.get(capability_id)


def capability_ids() -> tuple[str, ...]:
    return tuple(sorted(CAPABILITIES))


def capabilities_by_risk(risk: RiskLevel) -> tuple[Capability, ...]:
    return tuple(item for item in _ALL if item.risk is risk)
