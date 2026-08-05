"""Finding windows: what they are, where they are, and which must not be touched.

Phase 2 stage 4, P2-WIN-08 (FR-240). The eyes for window management, in the same
shape as `jarvis.toolbox.uia`: read-only, injectable backend, and every piece of
application-authored text treated as untrusted.

Two things here are load-bearing beyond "it lists windows".

**A window title is untrusted content.** It is written by the application, so it
gets the same handling as web page text and accessible names — carried out as an
`ObservedList`, addressed by position, never used to decide what an action lands
on. A desktop window feels more trustworthy than a web page; it is not.

**A blocked window is listed, with its title withheld.** Not hidden — hiding it
would mean Jarvis cannot say why it will not act, and ADR-0010 requires naming
what is not possible. Not shown either: a title like "Chase — personal banking"
is exactly the content the blocklist exists to keep out of prompts and logs. So
the window is present, the title is redacted, and the entry says it is sensitive.
That is the same choice made for password fields, for the same reason.
"""

from __future__ import annotations

import inspect

import pytest

from jarvis.core.observations import ContentClass
from jarvis.toolbox.sensitive import PASSWORD_REDACTION, SensitiveTargets
from jarvis.toolbox.windows import (
    SENSITIVE_TITLE_REDACTION,
    WindowDiscovery,
    WindowInfo,
    WindowState,
    WindowsUnavailable,
)


class FakeBackend:
    """A desktop that is whatever the test says it is."""

    def __init__(self, windows: list[dict] | None = None, reason: str | None = None) -> None:
        self._windows = windows if windows is not None else []
        self._reason = reason

    def is_available(self) -> bool:
        return self._reason is None

    def unavailable_reason(self) -> str | None:
        return self._reason

    def list_windows(self) -> list[dict]:
        return list(self._windows)


def _window(**overrides) -> dict:
    base = {
        "handle": 1001,
        "title": "YouTube — Brave",
        "process_name": "brave.exe",
        "pid": 4242,
        "bounds": (0, 0, 1920, 1080),
        "state": "normal",
        "monitor": 0,
    }
    base.update(overrides)
    return base


# =========================================================================
# Discovery
# =========================================================================
def test_windows_are_described_by_identity_position_and_state() -> None:
    discovery = WindowDiscovery(backend=FakeBackend([_window()]))

    found = discovery.list_windows()

    assert len(found) == 1
    window = found[0]
    assert isinstance(window, WindowInfo)
    assert window.process_name == "brave.exe"
    assert window.pid == 4242
    assert window.bounds == (0, 0, 1920, 1080)
    assert window.state is WindowState.NORMAL
    assert window.index == 0


def test_states_are_read_not_guessed() -> None:
    discovery = WindowDiscovery(
        backend=FakeBackend(
            [
                _window(handle=1, state="minimised"),
                _window(handle=2, state="maximised"),
                _window(handle=3, state="normal"),
            ]
        )
    )
    assert [w.state for w in discovery.list_windows()] == [
        WindowState.MINIMISED,
        WindowState.MAXIMISED,
        WindowState.NORMAL,
    ]


def test_an_unreadable_desktop_says_so_rather_than_reporting_no_windows() -> None:
    """"there are no windows" and "I cannot see windows" are different facts."""
    discovery = WindowDiscovery(backend=FakeBackend(reason="this is not Windows"))

    with pytest.raises(WindowsUnavailable) as raised:
        discovery.list_windows()
    assert "not Windows" in str(raised.value)


def test_an_empty_desktop_is_an_empty_list_not_an_error() -> None:
    assert WindowDiscovery(backend=FakeBackend([])).list_windows() == []


# =========================================================================
# Titles are untrusted content
# =========================================================================
def test_titles_leave_as_untrusted_positional_content() -> None:
    discovery = WindowDiscovery(backend=FakeBackend([_window(), _window(handle=2)]))

    observed = discovery.as_observed_list()

    assert observed.content_class is ContentClass.UI_TEXT
    assert len(observed.items) == 2
    assert observed.items[1].index == 1
    # The handle an action uses is derived from position, never from the title.
    assert "YouTube" not in observed.items[0].handle


def test_there_is_no_lookup_by_title() -> None:
    """The control the phase rests on, asserted structurally.

    A `find_by_title` would let a window choose what an action lands on by
    renaming itself — the desktop version of the defect
    `tests/security/test_prompt_injection.py` exists to prevent.
    """
    names = {name for name, _ in inspect.getmembers(WindowDiscovery, inspect.isfunction)}
    forbidden = {"find_by_title", "by_title", "search", "match_title", "find"}
    assert not forbidden & names, f"a title-based lookup exists: {forbidden & names}"


# =========================================================================
# Sensitive windows: listed, redacted, refused
# =========================================================================
def test_a_sensitive_window_is_listed_with_its_title_withheld() -> None:
    """Present, so Jarvis can say why it will not act (ADR-0010).

    Withheld, because a title is exactly the kind of content the blocklist
    exists to keep out of prompts and logs.
    """
    discovery = WindowDiscovery(
        backend=FakeBackend(
            [
                _window(),
                _window(
                    handle=2,
                    process_name="1Password.exe",
                    title="Chase — personal banking",
                ),
            ]
        )
    )

    found = discovery.list_windows()

    assert len(found) == 2, "a sensitive window was hidden rather than redacted"
    blocked = found[1]
    assert blocked.sensitive is True
    assert blocked.title == SENSITIVE_TITLE_REDACTION
    assert "Chase" not in repr(found)
    # Identity is still reported: it is what the refusal will name.
    assert blocked.process_name == "1Password.exe"


def test_redacting_a_sensitive_window_does_not_renumber_the_others() -> None:
    """Same rule as password fields: positions are what actions address."""
    discovery = WindowDiscovery(
        backend=FakeBackend(
            [
                _window(handle=1, title="first"),
                _window(handle=2, process_name="keepassxc.exe", title="secret"),
                _window(handle=3, title="third"),
            ]
        )
    )

    found = discovery.list_windows()

    assert [w.index for w in found] == [0, 1, 2]
    assert found[2].title == "third"


def test_an_ordinary_window_keeps_its_title() -> None:
    discovery = WindowDiscovery(backend=FakeBackend([_window()]))
    assert discovery.list_windows()[0].title == "YouTube — Brave"
    assert discovery.list_windows()[0].sensitive is False


def test_the_blocklist_is_injectable_so_the_user_can_widen_it() -> None:
    discovery = WindowDiscovery(
        backend=FakeBackend([_window(process_name="notepad.exe", title="notes")]),
        sensitive=SensitiveTargets(blocked_processes={"notepad.exe"}),
    )
    assert discovery.list_windows()[0].sensitive is True


def test_a_sensitive_title_never_reaches_the_observed_list() -> None:
    """The boundary the model actually reads."""
    discovery = WindowDiscovery(
        backend=FakeBackend([_window(process_name="bitwarden.exe", title="my vault")])
    )
    observed = discovery.as_observed_list()
    assert "my vault" not in repr(observed)
    assert observed.items[0].label == SENSITIVE_TITLE_REDACTION


def test_the_two_redaction_markers_are_distinguishable() -> None:
    """A window and a password field are different things to have withheld."""
    assert SENSITIVE_TITLE_REDACTION != PASSWORD_REDACTION
