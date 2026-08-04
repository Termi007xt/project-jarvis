"""Every registered tool's declared contract must actually be usable.

`voice.speak` declared `resource_locks=("audio_output",)`. There is no such
lock — the vocabulary calls it `speaker_output` — so every attempt to speak
died inside the invoker with a raw `ValueError` that reached the user as:

    Jarvis could not answer: ValueError: unknown resource lock 'audio_output'.

The tool's own tests passed, because they called `run()` directly and never went
through the invoker's lock step. Nothing checked a `ToolSpec` against the
vocabularies it references, so a typo in a declaration was invisible until a
human tried the feature.

These tests check the declarations themselves, for every tool the product
registers, so the next typo fails the build instead of the user.
"""

from __future__ import annotations

import pytest

from jarvis.core.permissions.models import RiskLevel
from jarvis.tasks.locks import validate_lock_name


def registered_specs(core) -> list:
    """Every spec the real core registers, plus the shell-only ones."""
    specs = list(core.registry.specs())
    assert specs, "the core registered no tools at all"
    return specs


# -- the defect -------------------------------------------------------------
def test_every_declared_resource_lock_exists(core) -> None:
    """A lock name the manager rejects makes the tool permanently unusable."""
    for spec in registered_specs(core):
        for lock in spec.resource_locks:
            try:
                validate_lock_name(lock)
            except ValueError as exc:
                pytest.fail(f"{spec.tool_id} declares an unusable lock: {exc}")


def test_speaking_takes_the_speaker_lock(core) -> None:
    """Named explicitly: this is the one that was wrong."""
    from jarvis.toolbox.phase1_tools import SpeakTool

    assert SpeakTool.spec.resource_locks == ("speaker_output",)


# -- Phase 2: nothing moves without owning the desktop ----------------------
#: Capabilities that drive the physical desktop. A tool holding one of these can
#: move the pointer, press keys, or act inside a browser that has the user's
#: focus — so it must own `foreground_desktop` first (FR-077, PRD §7.1).
INPUT_OWNING_CAPABILITIES = frozenset(
    {
        "input.automate",
        "browser.automate_logged_in",
    }
)


def test_a_tool_that_moves_anything_must_own_the_desktop_first(core) -> None:
    """FR-077, and the Phase 2 rule that must not be retrofitted.

    Two tasks driving the mouse at once produce garbage that is very hard to
    diagnose afterwards, and a tool that takes input without the lock also
    cannot be paused by the user-interruption path (FR-078, AT-008), because
    that path works by refusing to hand the lock over.

    This is asserted against the declaration rather than the implementation on
    purpose. `voice.speak` proves the point: its *behaviour* was correct and its
    *declaration* named a lock that did not exist, and nothing noticed until a
    human tried to use it.
    """
    from jarvis.tasks.locks import FOREGROUND_DESKTOP

    for spec in registered_specs(core):
        owning = INPUT_OWNING_CAPABILITIES & set(spec.required_capabilities)
        if not owning:
            continue
        assert FOREGROUND_DESKTOP in spec.resource_locks, (
            f"{spec.tool_id} declares {sorted(owning)} but does not take the "
            f"'{FOREGROUND_DESKTOP}' lock. Anything that drives the pointer or "
            "keyboard must own the desktop first, or two tasks will fight over "
            "it and the user cannot interrupt either (FR-077, FR-078)."
        )


def test_the_input_owning_capabilities_are_real() -> None:
    """Guard against this rule quietly becoming vacuous.

    If a capability here were renamed in the catalogue and not here, the check
    above would silently match nothing and keep passing — a green test asserting
    an empty set, which is the failure mode this project keeps meeting.
    """
    from jarvis.core.permissions.catalogue import CAPABILITIES

    unknown = INPUT_OWNING_CAPABILITIES - set(CAPABILITIES)
    assert not unknown, (
        f"{sorted(unknown)} are not in the capability catalogue, so the "
        "desktop-ownership rule matches nothing and proves nothing"
    )


def test_every_tool_can_be_invoked_without_a_contract_error(core) -> None:
    """The invoker validates locks before doing anything. Prove it passes."""
    from jarvis.core.tools.invoker import ToolCall

    for spec in registered_specs(core):
        # An empty parameter set fails schema validation, which is fine and
        # expected. What must NOT happen is a ValueError from the lock step.
        result = core.invoker.invoke(ToolCall(tool_id=spec.tool_id, parameters={}))
        assert result is not None
        detail = f"{result.outcome} {result.message} {result.failure_code or ''}"
        assert "unknown resource lock" not in detail, (
            f"{spec.tool_id} cannot be invoked at all: {detail}"
        )


# -- the rest of the declared contract -------------------------------------
def test_every_tool_declares_the_capabilities_it_needs(core) -> None:
    for spec in registered_specs(core):
        assert spec.required_capabilities, f"{spec.tool_id} declares no capability"


def test_every_tool_declares_a_risk_level(core) -> None:
    for spec in registered_specs(core):
        assert isinstance(spec.risk, RiskLevel)


def test_every_tool_declares_a_bounded_timeout(core) -> None:
    """CLAUDE.md: every external interaction declares a timeout."""
    for spec in registered_specs(core):
        assert spec.timeout_seconds and spec.timeout_seconds > 0, (
            f"{spec.tool_id} has no timeout"
        )


def test_every_tool_declares_how_it_verifies_itself(core) -> None:
    """FR-048: `succeeded` requires verification, so it must be described."""
    for spec in registered_specs(core):
        assert spec.verification and spec.verification.strip(), (
            f"{spec.tool_id} does not say how it verifies its own effect"
        )


def test_every_tool_declares_its_failure_codes(core) -> None:
    """The invoker rejects an undeclared code, turning a handled failure into
    a crash, so an empty list is only correct for a tool that cannot fail."""
    for spec in registered_specs(core):
        assert isinstance(spec.failure_codes, tuple)


def test_capability_names_are_known_to_the_catalogue(core) -> None:
    """A capability the catalogue has never heard of can never be granted."""
    from jarvis.core.permissions.catalogue import capability

    for spec in registered_specs(core):
        for name in spec.required_capabilities:
            assert capability(name) is not None, (
                f"{spec.tool_id} needs '{name}', which is not in the catalogue"
            )
