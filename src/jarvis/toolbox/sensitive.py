"""What automation must refuse to touch (FR-079, FR-080, FR-081, AT-031).

Phase 2 stage 4, written before window actions and screen capture exist. Stage 1
built the untrusted-content boundary before anything could fetch a page and the
test found a real defect the same day; a blocklist written after capture works
is a blocklist nobody notices is porous.

**The asymmetry is the design.** A refusal keys on *process identity*, which
comes from the operating system. A window title does not: it is authored by the
application, which makes it exactly as untrusted as the text on a web page or
the accessible name of a control (`jarvis.core.observations`, `jarvis.toolbox.uia`).
So a title may **add** a refusal and may never remove one. Get that backwards and
the way past the password-manager blocklist is a `SetWindowText` call — made by
the very party the block exists to constrain.

**Password fields are redacted, never dropped.** Removing an element renumbers
every element after it, and positional selection is the control this whole phase
rests on. A redaction that shifts indices is a redaction that moves the target of
the next action.

There is deliberately no override, no `force`, and no `allow_sensitive`. A
refusal with a bypass parameter is a refusal the model can be argued into
skipping, and `tests/security/test_sensitive_targets.py` asserts the absence
structurally rather than trusting that nobody adds one later.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence, TypeVar

__all__ = [
    "SensitiveTargets",
    "SensitivityVerdict",
    "DEFAULT_BLOCKED_PROCESSES",
    "DEFAULT_BLOCKED_TITLE_MARKERS",
    "PASSWORD_REDACTION",
    "redact_password_fields",
    "secure_desktop_active",
]

_LOG = logging.getLogger(__name__)

#: Applications automation never drives and capture never photographs.
#:
#: Credential stores, the Windows credential and consent prompts, and the lock
#: screen. These are matched on the executable name the OS reports, so an
#: application cannot rename its way off the list.
DEFAULT_BLOCKED_PROCESSES: frozenset[str] = frozenset(
    {
        # Password and secret managers
        "1password.exe", "bitwarden.exe", "keepass.exe", "keepassxc.exe",
        "lastpass.exe", "dashlane.exe", "enpass.exe", "protonpass.exe",
        "nordpass.exe", "roboform.exe", "keeper.exe",
        # Windows credential, consent and logon surfaces. `consent.exe` is the
        # UAC prompt itself; it runs on the secure desktop and is unreachable
        # anyway, and refusing it by name means the refusal is a decision rather
        # than an accident of what Windows happens to permit.
        "credentialuibroker.exe", "consent.exe", "logonui.exe", "lsass.exe",
        "securityhealthhost.exe", "securityhealthsystray.exe",
        # Authenticators and hardware key tools
        "winauth.exe", "authy desktop.exe", "yubikey manager.exe",
    }
)

#: Title fragments that make *any* window sensitive, whatever process owns it.
#:
#: One-way only. An ordinary browser showing "Enter your recovery phrase" is
#: worth refusing; the same browser showing "Nothing sensitive here" gets no
#: credit for saying so.
DEFAULT_BLOCKED_TITLE_MARKERS: frozenset[str] = frozenset(
    {
        "password", "passphrase", "seed phrase", "recovery phrase",
        "private key", "secret key", "credential", "authenticator",
        "one-time code", "one time code", "verification code",
        "two-factor", "2fa", "sign in", "log in", "banking",
    }
)

#: What replaces the contents of a password field. A fixed marker, so it is
#: obvious in a log or a transcript that something was removed on purpose
#: rather than that the field was empty.
PASSWORD_REDACTION = "[password field — not read]"


@dataclass(frozen=True)
class SensitivityVerdict:
    """Whether a target may be automated or captured, and what decided it."""

    allowed: bool
    reason: str
    #: What matched, for the audit log. Never the window's contents.
    matched: str | None = None


class SensitiveTargets:
    """The blocklist. Refuses; never grants.

    Both lists are configurable, because what counts as sensitive is the user's
    call — but neither can be emptied into an override at a call site, and there
    is no method here that turns a refusal back into permission.
    """

    def __init__(
        self,
        blocked_processes: Iterable[str] | None = None,
        blocked_title_markers: Iterable[str] | None = None,
    ) -> None:
        self._processes = frozenset(
            name.casefold() for name in (blocked_processes or DEFAULT_BLOCKED_PROCESSES)
        )
        self._titles = frozenset(
            marker.casefold()
            for marker in (blocked_title_markers or DEFAULT_BLOCKED_TITLE_MARKERS)
        )

    def check(self, *, process_name: str, window_title: str) -> SensitivityVerdict:
        """Decide whether this window may be automated or captured.

        Process first and by basename, so a full path or different
        capitalisation cannot slip past. Only then the title, and only ever to
        add a refusal.
        """
        executable = Path(process_name.strip()).name.casefold()
        if executable in self._processes:
            return SensitivityVerdict(
                allowed=False,
                reason=(
                    f"'{executable}' is on the sensitive-application list, so "
                    "Jarvis will not automate it or photograph its window. "
                    "This one cannot be approved at the time of asking; the "
                    "list is editable in Settings."
                ),
                matched=executable,
            )

        # The title is the application's own account of itself. It is read only
        # to find *more* reasons to refuse — never to clear one, which is why
        # this runs after the process check and cannot reach an `allowed=False`.
        lowered = window_title.casefold()
        for marker in sorted(self._titles):
            if marker in lowered:
                return SensitivityVerdict(
                    allowed=False,
                    reason=(
                        f"this window describes itself as containing '{marker}', "
                        "so it is treated as sensitive and is not automated or "
                        "captured."
                    ),
                    matched=marker,
                )

        return SensitivityVerdict(allowed=True, reason="not a sensitive target")


_Field = TypeVar("_Field")


def redact_password_fields(fields: Sequence[_Field]) -> list[_Field]:
    """Blank the contents of password fields, keeping every position (FR-080).

    In place, deliberately. Dropping the element would renumber everything after
    it, and "click the third button" is resolved by that number — so a
    redaction that removes is a redaction that silently retargets the next
    action.

    Returns copies; the input is not modified, so a caller holding the original
    snapshot does not find it altered underneath them.
    """
    from copy import copy

    redacted: list[_Field] = []
    for field in fields:
        if getattr(field, "is_password", False):
            replacement = copy(field)
            try:
                replacement.name = PASSWORD_REDACTION  # type: ignore[attr-defined]
            except AttributeError:
                # A frozen element: rebuild it rather than leaking the value by
                # failing open. Refusing to redact is not an option here.
                replacement = field.__class__(  # type: ignore[call-arg]
                    **{**vars(field), "name": PASSWORD_REDACTION}
                )
            redacted.append(replacement)
        else:
            redacted.append(field)
    return redacted


def secure_desktop_active() -> bool:
    """Whether Windows has switched to a secure desktop (FR-079).

    A UAC prompt, the lock screen and the Ctrl+Alt+Del screen all run on a
    desktop that ordinary processes cannot reach. Automation there is impossible
    by design and that is a good thing — but *appearing to try* and silently
    doing nothing is the failure mode ADR-0010 exists to prevent, so this is
    checked and reported rather than discovered as an inexplicable no-op.

    Returns False off Windows and whenever the answer cannot be established: the
    caller has other reasons to refuse, and inventing a secure desktop that is
    not there would block ordinary work.
    """
    if os.name != "nt":
        return False
    try:
        import ctypes

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        # The *input* desktop is the one receiving keystrokes. When UAC is up it
        # is "Winlogon" rather than "Default", and OpenInputDesktop fails
        # outright for an unprivileged process — which is itself the answer.
        desktop = user32.OpenInputDesktop(0, False, 0x0100)  # DESKTOP_READOBJECTS
        if not desktop:
            return True
        try:
            buffer = ctypes.create_unicode_buffer(256)
            needed = ctypes.c_ulong()
            # UOI_NAME = 2
            if not user32.GetUserObjectInformationW(
                desktop, 2, buffer, ctypes.sizeof(buffer), ctypes.byref(needed)
            ):
                return True
            return buffer.value.casefold() != "default"
        finally:
            user32.CloseDesktop(desktop)
    except Exception:  # noqa: BLE001 - an unanswerable probe is not a prompt
        _LOG.debug("could not read the input desktop", exc_info=True)
        return False
