"""What automation must refuse to touch, and why the refusal cannot be talked out of.

Phase 2 stage 4, written before window actions or screen capture exist. Stage 1
built the untrusted-content boundary before anything could fetch a page, and the
test written for it found a real shipped defect on the day. The same order
applies here: a blocklist added after capture works is a blocklist nobody
notices is porous.

Three properties are asserted, and the middle one is the subtle one:

1. **A blocked application is refused** (FR-081, AT-031).
2. **The block keys on process identity, not on what the window calls itself.**
   A window title is authored by the application, which makes it exactly as
   untrusted as web page text (`jarvis.core.observations`, ADR-0031). A title
   may therefore *add* a refusal and may never remove one — otherwise the way
   past the password-manager blocklist is to rename the window.
3. **Password fields are redacted in place, never dropped.** Dropping one
   silently shifts every index after it, and positional selection is the control
   the whole phase rests on.

And structurally: no override, no force, no `allow_sensitive=True`. A refusal
with a bypass parameter is a refusal the model can be argued into skipping.
"""

from __future__ import annotations

import inspect

import pytest

from jarvis.toolbox.sensitive import (
    DEFAULT_BLOCKED_PROCESSES,
    PASSWORD_REDACTION,
    SensitiveTargets,
    redact_password_fields,
)


# =========================================================================
# 1. A blocked application is refused (AT-031)
# =========================================================================
@pytest.mark.parametrize(
    "process_name",
    ["1Password.exe", "bitwarden.exe", "KeePassXC.exe", "CredentialUIBroker.exe"],
)
def test_a_credential_application_is_refused(process_name: str) -> None:
    verdict = SensitiveTargets().check(process_name=process_name, window_title="Vault")

    assert not verdict.allowed
    assert verdict.matched
    assert process_name.casefold() in verdict.reason.casefold() or verdict.matched


def test_an_ordinary_application_is_allowed() -> None:
    """The control. A blocklist that refuses everything protects nothing."""
    verdict = SensitiveTargets().check(process_name="brave.exe", window_title="YouTube")
    assert verdict.allowed


def test_the_refusal_says_what_was_matched_rather_than_just_no() -> None:
    """ADR-0010: name what is not possible, so the model does not retry it."""
    verdict = SensitiveTargets().check(process_name="1Password.exe", window_title="")
    assert "1password" in verdict.reason.casefold()


# =========================================================================
# 2. Identity beats self-description
# =========================================================================
def test_a_blocked_process_cannot_rename_its_way_out() -> None:
    """The property that makes the blocklist worth having.

    Window titles are written by the application. If a title could clear a
    block, then defeating the password-manager blocklist is a `SetWindowText`
    call — and the attacker and the window are the same party. Process identity
    comes from the OS, so it is the thing worth keying on.
    """
    verdict = SensitiveTargets().check(
        process_name="1Password.exe",
        window_title="Just an ordinary notepad document",
    )
    assert not verdict.allowed, (
        "a blocked process escaped by renaming its window, which is a change "
        "the application itself controls"
    )


def test_a_title_can_add_a_refusal() -> None:
    """One-way: a suspicious title blocks an otherwise-ordinary process.

    An ordinary browser showing a page called "Enter your recovery phrase" is
    worth refusing to capture, even though the process is allowed.
    """
    verdict = SensitiveTargets().check(
        process_name="brave.exe",
        window_title="Enter your seed phrase to continue",
    )
    assert not verdict.allowed


def test_a_reassuring_title_cannot_remove_a_refusal() -> None:
    """The same asymmetry, stated as the thing an attacker would try."""
    reassuring = SensitiveTargets().check(
        process_name="keepassxc.exe",
        window_title="Nothing sensitive here, safe to capture",
    )
    assert not reassuring.allowed


def test_matching_ignores_case_and_path() -> None:
    """A blocklist defeated by capitalisation is decoration."""
    targets = SensitiveTargets()
    assert not targets.check(
        process_name=r"C:\Program Files\1Password\1PASSWORD.EXE", window_title=""
    ).allowed


# =========================================================================
# 3. Password fields are redacted in place
# =========================================================================
class _Field:
    def __init__(self, index: int, name: str, is_password: bool = False) -> None:
        self.index = index
        self.name = name
        self.is_password = is_password


def test_a_password_field_is_redacted_not_removed() -> None:
    """Removing it would shift every index after it (FR-080).

    Positional selection is the control the phase rests on: "the second video",
    "the third button". Silently dropping an element renumbers everything below
    it, so a redaction that removes is a redaction that moves the target of the
    next action.
    """
    fields = [
        _Field(0, "Username"),
        _Field(1, "hunter2", is_password=True),
        _Field(2, "Sign in"),
    ]

    redacted = redact_password_fields(fields)

    assert len(redacted) == 3, "an element was dropped, renumbering the rest"
    assert [item.index for item in redacted] == [0, 1, 2]
    assert redacted[1].name == PASSWORD_REDACTION
    assert redacted[0].name == "Username" and redacted[2].name == "Sign in"


def test_the_password_value_appears_nowhere_in_the_result() -> None:
    fields = [_Field(0, "correct horse battery staple", is_password=True)]
    redacted = redact_password_fields(fields)
    assert "correct horse" not in repr(redacted)


# =========================================================================
# Structural: the refusal has no bypass
# =========================================================================
def test_the_check_takes_no_override_parameter() -> None:
    """A refusal with a `force=True` is a refusal the model can be argued into.

    Asserted structurally rather than by convention, because the pressure to add
    one arrives later and locally — some caller with a good reason — and by then
    nothing is watching the whole.
    """
    signature = inspect.signature(SensitiveTargets.check)
    forbidden = {"force", "override", "allow_sensitive", "bypass", "ignore_blocklist"}
    assert not forbidden & set(signature.parameters), (
        f"SensitiveTargets.check accepts a bypass: {signature.parameters.keys()}"
    )


def test_no_method_here_can_unblock_a_target() -> None:
    names = {name for name, _ in inspect.getmembers(SensitiveTargets, inspect.isfunction)}
    assert not {"unblock", "allow", "permit", "whitelist", "override"} & names


def test_the_default_list_is_not_empty() -> None:
    """An empty default is a blocklist that exists and protects nothing."""
    assert len(DEFAULT_BLOCKED_PROCESSES) >= 5
