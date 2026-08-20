"""Phase 2 exit criteria (P2-COR-01, P2-TST-01).

The checklist for closing the phase, in the same shape as
`test_phase0_exit_criteria.py`: if this file is green, Phase 2 is done in the
sense the PRD means, and what it is *not* claiming is written down beside what
it is.

**P2-COR-01 is the one worth reading.** "Honest completion enforced against real
verifiable actions" was a paragraph in the backlog until 2026-08-06, when the
owner spent a day finding out what it meant in practice. Five separate failures,
all the same shape — something reported success it had not earned, because the
check it ran could not distinguish *"I did this"* from *"this was already
true"*:

* a window listing licensed "MS Edge has been closed";
* `app.close` verified against a list that drops hidden windows, so Chromium
  hiding its frame read as a successful close;
* a verified `app.open` carried "and playing the current song";
* a launch verified against "is Brave running", which it already was;
* "bring to the front" verified against "is it not minimised", which it was not.

So the criterion is asserted here as invariants over the *registered* tool set
rather than as a story about one action. A tool added next month is covered.
"""

from __future__ import annotations

import pytest

from jarvis.core.tools.contract import Verification
from jarvis.runtime.core import JarvisCore


# =========================================================================
# P2-COR-01 — a success claim is earned, structurally
# =========================================================================
def test_every_state_changing_tool_declares_how_it_verifies(core: JarvisCore) -> None:
    """FR-048. A tool that changes something must say how it knows it worked."""
    for spec in core.registry.specs():
        if spec.changes_state:
            assert spec.verification.strip(), (
                f"{spec.tool_id} changes state and declares no verification. "
                "'succeeded' would then mean 'the call returned'."
            )


def test_a_read_only_tool_can_never_report_verified(core: JarvisCore) -> None:
    """The rule that closed the 2026-08-06 hole, asserted at the choke point.

    `window.list` declared `changes_state=False` and returned `verified`, and
    the grounding layer reads any verified result as licence for a reply to
    claim an action happened. "I verified that I listed your windows" became
    "I closed Edge", twice, with Edge still on screen.

    Enforced in `ToolInvoker` rather than per tool, so this holds for tools that
    do not exist yet.
    """
    import inspect

    from jarvis.core.tools import invoker as invoker_module

    source = inspect.getsource(invoker_module)
    assert "not spec.changes_state" in source and "NOT_APPLICABLE" in source, (
        "the invoker no longer normalises a read-only tool's verification; a "
        "listing can license a claim that something was done"
    )


def test_unverified_is_a_distinct_outcome_and_not_a_soft_success() -> None:
    """It must not collapse into either neighbour.

    If `unverified` compared equal to `verified` the honesty is decorative; if
    it compared equal to `failed`, every close that stopped on a save prompt
    would read as broken and the user would learn to ignore it.
    """
    assert Verification.UNVERIFIED is not Verification.VERIFIED
    assert Verification.UNVERIFIED is not Verification.FAILED
    assert len({v.value for v in Verification}) == len(list(Verification))


def test_a_high_risk_tool_is_never_reversible_by_declaration(core: JarvisCore) -> None:
    """Force-close loses work. Nothing may claim that is undoable."""
    from jarvis.core.permissions.models import RiskLevel

    for spec in core.registry.specs():
        if spec.risk is RiskLevel.HIGH:
            assert spec.reversible is False, (
                f"{spec.tool_id} is high risk and declares itself reversible"
            )


def test_every_tool_declares_its_failure_codes(core: JarvisCore) -> None:
    """An invented failure code is a failure nobody can handle or test."""
    for spec in core.registry.specs():
        assert spec.failure_codes or not spec.changes_state, (
            f"{spec.tool_id} changes state and declares no failure codes"
        )


# =========================================================================
# P2-TST-01 — the phase's capabilities are actually reachable
# =========================================================================
PHASE_2_TOOLS = {
    "youtube.search": "search YouTube and get indexed results",
    "youtube.play": "play a result by position",
    "browser.restart": "reopen the browser so automation can attach",
    "window.list": "see what is open",
    "window.arrange": "move, snap, minimise, maximise",
    "screen.active_window": "say what the user is looking at",
    "app.close": "ask an application to close",
    "app.force_close": "terminate it, with fresh confirmation every time",
    "files.find": "search the approved folders",
    "files.reveal": "point at a result in Explorer",
    "files.open": "open a result with an approved application",
}


def test_every_phase_2_capability_is_registered(core: JarvisCore) -> None:
    """The seam, at phase level.

    This project has shipped a correct mechanism wired to nothing six times.
    Every one passed its own unit tests, so the only test that would have caught
    them is one that asks whether the assembled product offers the thing.
    """
    registered = set(core.registry.tool_ids())
    missing = {
        tool: purpose
        for tool, purpose in PHASE_2_TOOLS.items()
        if tool not in registered
    }

    assert not missing, f"built but not reachable from the running product: {missing}"


def test_screen_capture_is_reachable_once_a_shell_exists(core: JarvisCore) -> None:
    """The exception, and it is deliberate.

    `screen.capture` is absent headless because Jarvis does not photograph the
    screen without something able to show that it is happening (FR-271). It is
    not missing; it is conditional, and the condition is the control.
    """
    assert core.registry.get("screen.capture") is None

    core.attach_shell(lambda _t, _m: True, lambda _m: None)

    assert core.registry.get("screen.capture") is not None


def test_no_phase_2_tool_selects_by_title_or_path(core: JarvisCore) -> None:
    """The injection defence, written into the signatures rather than a rule.

    Every Phase 2 tool that acts on something the user can see addresses it by
    an engine-issued reference or a position. A page, a window and a file all
    choose their own names, so a name is never a selector — which is why none of
    these tools has a parameter that would accept one.
    """
    forbidden = {"title", "path", "filename", "file", "url_text", "name"}
    exempt = {
        # Names an application from the catalogue, which is a choice among
        # approved entries — never a binary and never a path (ADR-0029).
        "app.open",
        "files.open",
        # Takes a URL by design, restricted to http/https at the catalogue.
        "web.open_url",
    }

    for spec in core.registry.specs():
        if spec.tool_id in exempt or spec.tool_id not in PHASE_2_TOOLS:
            continue
        fields = set(spec.input_model.model_fields)
        assert not fields & forbidden, (
            f"{spec.tool_id} can be pointed at something by name: "
            f"{sorted(fields & forbidden)}"
        )


def test_the_phase_declares_what_it_did_not_build(core: JarvisCore) -> None:
    """ADR-0010, at phase level: name what is not possible.

    Reading a file's contents, describing what is on screen, and controlling
    YouTube Music are all things a person would reasonably expect from what
    Phase 2 *does* offer. None is built, and the failure mode this guards
    against is not a missing feature — it is a tool whose description implies a
    capability next to it.
    """
    descriptions = {
        spec.tool_id: spec.description.lower() for spec in core.registry.specs()
    }

    assert "does not read what is inside" in descriptions["files.find"]
    assert "cannot read" in descriptions["screen.active_window"]
    assert "not the way to control the youtube music" in descriptions["youtube.play"]


@pytest.mark.parametrize(
    "issue",
    [
        "Opening the browser wakes every other tab",
        '"YouTube Music" plays the wrong thing',
        "Screenshot retention is a bound, not a policy",
    ],
)
def test_the_known_issues_file_still_names_the_open_defects(issue: str) -> None:
    """A limitation that stops being written down stops being known.

    Each of these was found by the owner and is still present. If one is fixed,
    this test is the reminder to move it to the resolved table rather than
    delete the entry.
    """
    from pathlib import Path

    text = Path(__file__).resolve().parents[2] / "docs" / "KNOWN_ISSUES.md"
    assert issue in text.read_text(encoding="utf-8"), (
        f"'{issue}' is no longer in KNOWN_ISSUES.md. If it was fixed, move it "
        "to the resolved table and update this list."
    )
