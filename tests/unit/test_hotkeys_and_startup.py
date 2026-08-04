"""Global hotkeys and start-at-sign-in (PRD section 11.3, FR-018, FR-002).

Parsing is pure logic and is tested everywhere. Registration needs a Windows
message loop and a key no other process owns, so it is not asserted here; what
*is* asserted is that a hotkey which cannot be registered reports itself
unavailable rather than appearing to work (ADR-0010).
"""

from __future__ import annotations

import os

import pytest

from jarvis.runtime.hotkeys import (
    GlobalHotkeys,
    HotkeyError,
    parse_hotkey,
)
from jarvis.runtime import startup

WINDOWS_ONLY = pytest.mark.skipif(os.name != "nt", reason="Windows-only facility")


# -- parsing ----------------------------------------------------------------
def test_the_emergency_stop_default_parses() -> None:
    """PRD section 11.3 and config/defaults.yaml agree on this combination."""
    hotkey = parse_hotkey("Ctrl+Alt+Pause")
    assert hotkey.text == "Ctrl+Alt+Pause"
    assert hotkey.modifiers & 0x0002  # MOD_CONTROL
    assert hotkey.modifiers & 0x0001  # MOD_ALT
    assert hotkey.virtual_key == 0x13  # VK_PAUSE


def test_the_push_to_talk_default_parses() -> None:
    """FR-018 and ADR-0027 specify bare F9, with no modifier."""
    hotkey = parse_hotkey("F9")
    assert hotkey.virtual_key == 0x78
    assert hotkey.text == "F9"


def test_every_function_key_is_bindable() -> None:
    for index in range(1, 25):
        assert parse_hotkey(f"F{index}").virtual_key == 0x6F + index


def test_repeat_is_always_suppressed() -> None:
    """An emergency stop that fires forty times is not better than one."""
    assert parse_hotkey("Ctrl+Alt+Pause").modifiers & 0x4000  # MOD_NOREPEAT


def test_parsing_is_case_and_spacing_insensitive() -> None:
    assert parse_hotkey("ctrl + ALT + pause").text == parse_hotkey("Ctrl+Alt+Pause").text


def test_the_windows_key_is_supported() -> None:
    assert parse_hotkey("Win+J").modifiers & 0x0008


@pytest.mark.parametrize(
    "text, message",
    [
        ("", "at least one key"),
        ("   ", "at least one key"),
        ("Ctrl+Alt", "only modifiers"),
        ("Ctrl+A+B", "more than one non-modifier"),
        ("Ctrl+Sparkle", "not a key this build can bind"),
    ],
)
def test_an_unusable_hotkey_says_exactly_what_is_wrong(text: str, message: str) -> None:
    with pytest.raises(HotkeyError, match=message):
        parse_hotkey(text)


# -- registration and honesty ----------------------------------------------
def test_a_disabled_manager_registers_nothing_and_says_so() -> None:
    fired: list[str] = []
    hotkeys = GlobalHotkeys(enabled=False)
    binding = hotkeys.add("emergency_stop", "Ctrl+Alt+Pause", lambda: fired.append("stop"))

    assert not hotkeys.available
    assert not binding.registered
    assert binding.error
    assert binding in hotkeys.unavailable()
    assert "unavailable" in binding.describe()


def test_an_unparseable_hotkey_is_reported_not_raised() -> None:
    """A bad setting must not stop the application starting."""
    hotkeys = GlobalHotkeys(enabled=False)
    binding = hotkeys.add("push_to_talk", "Ctrl+Nonsense", lambda: None)
    assert not binding.registered
    assert "not a key this build can bind" in (binding.error or "")


def test_starting_a_disabled_manager_is_a_no_op() -> None:
    hotkeys = GlobalHotkeys(enabled=False)
    hotkeys.add("push_to_talk", "F9", lambda: None)
    hotkeys.start()
    hotkeys.stop()
    assert not any(binding.registered for binding in hotkeys.bindings())


def test_a_binding_can_be_triggered_directly() -> None:
    """The tray and the tests need a route that does not need a real keypress."""
    fired: list[str] = []
    hotkeys = GlobalHotkeys(enabled=False)
    hotkeys.add("emergency_stop", "Ctrl+Alt+Pause", lambda: fired.append("stop"))

    assert hotkeys.trigger("emergency_stop") is True
    assert fired == ["stop"]
    assert hotkeys.trigger("no_such_binding") is False


def test_bindings_are_addressable_by_name() -> None:
    hotkeys = GlobalHotkeys(enabled=False)
    hotkeys.add("push_to_talk", "F9", lambda: None)
    assert hotkeys.binding("push_to_talk") is not None
    assert hotkeys.binding("missing") is None


# -- start at sign-in (FR-002) ---------------------------------------------
def test_availability_matches_the_platform() -> None:
    assert startup.available() is (os.name == "nt")


def test_the_description_is_honest_about_what_it_does() -> None:
    described = startup.describe()
    assert described.note
    if described.supported:
        # Phase 6 replaces this with a packaged executable (ADR-0013).
        assert "administrator" in described.note
        assert ".venv" in described.note
    else:
        assert "Windows" in described.note


@pytest.mark.skipif(os.name == "nt", reason="covers the non-Windows path")
def test_off_windows_it_reports_unsupported_rather_than_failing() -> None:
    assert startup.is_enabled() is False
    assert startup.set_enabled(True).supported is False
    assert startup.is_enabled() is False


@WINDOWS_ONLY
def test_the_startup_command_points_at_an_interpreter_that_exists() -> None:
    from pathlib import Path

    command = startup._startup_command()  # noqa: SLF001
    assert command.startswith('"')
    interpreter = Path(command.split('"')[1])
    assert interpreter.exists()
    assert "-m jarvis.main" in command


@WINDOWS_ONLY
def test_enabling_then_disabling_leaves_no_entry() -> None:
    """Runs against the real per-user Run key, and cleans up after itself."""
    was_enabled = startup.is_enabled()
    try:
        startup.set_enabled(True)
        assert startup.is_enabled() is True
        startup.set_enabled(False)
        assert startup.is_enabled() is False
        # Removing something already absent is not an error.
        assert startup.set_enabled(False).enabled is False
    finally:
        startup.set_enabled(was_enabled)
