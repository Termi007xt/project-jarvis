"""Listing something is not doing something (FR-047, FR-048, AT-018).

Reported by the owner on 2026-08-06, and the audit log settles what happened:

    13:58:29  window.list        succeeded   verified
    -- Jarvis: "The MS Edge window has been closed successfully."
    13:59:24  window.list        succeeded   verified
    -- Jarvis: "The MS Edge window ... has been closed successfully!"

**No close tool ran in either turn.** The model listed the windows and then
described a close it had never performed — twice — and both replies reached the
owner marked *"confirmed by a tool"*. Edge was open throughout.

There are two failures here and only one of them is the model's.

`jarvis.llm.grounding` exists precisely to stop a reply claiming an unverified
success, and it did not fire. Its rule is that a success claim needs a
``verified`` tool result, and its docstring says why that is safe: *"a read-only
tool cannot confirm that anything was done"*, because a read-only tool reports
``not_applicable``. That reasoning is correct and the premise was false —
``window.list`` declares ``changes_state=False`` and returned ``VERIFIED``. So
"I verified that I listed your windows" was read as licence for "I closed Edge".

The invoker already enforces the mirror image of this rule: a state-changing
tool that reports ``not_applicable`` is downgraded to ``unverified``, because
changing something without confirming it is not success. The direction that was
missing is the one that bit: **a tool that changes nothing has nothing to
verify**, whatever it says about itself.

Fixed at the invoker rather than in each tool, because that is the single point
every effect passes through, and a rule enforced per-tool is a rule the next
tool forgets.
"""

from __future__ import annotations

from jarvis.core.tools.contract import (
    RetryPolicy,
    ToolExecution,
    ToolSpec,
    Verification,
)
from jarvis.core.permissions.models import RiskLevel
from jarvis.llm.grounding import SourceLabel, review_response
from pydantic import BaseModel, ConfigDict


class _Empty(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class _Listing(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    count: int = 0


class OverclaimingReadOnlyTool:
    """A read-only tool that says it verified something. Like `window.list` did."""

    spec = ToolSpec(
        tool_id="test.listing",
        version="1.0.0",
        description="List things. Changes nothing.",
        input_model=_Empty,
        output_model=_Listing,
        risk=RiskLevel.LOW,
        required_capabilities=("window.read_layout",),
        resource_locks=(),
        timeout_seconds=5.0,
        retry_policy=RetryPolicy(max_attempts=1),
        changes_state=False,
        verification="Reports what was listed.",
        failure_codes=("listing_failed",),
        reversible=True,
    )

    def run(self, context, parameters) -> ToolExecution:
        return ToolExecution(
            output=_Listing(count=3),
            verification=Verification.VERIFIED,
            message="listed 3 things",
        )


class _Result:
    """The shape `review_response` reads: a succeeded ToolResult."""

    def __init__(self, verification: Verification, tool_id: str = "window.list") -> None:
        self.succeeded = True
        self.verification = verification
        self.tool_id = tool_id


# =========================================================================
# A tool that changes nothing has nothing to verify
# =========================================================================
def test_a_read_only_tool_cannot_report_verified(
    registry, permissions, audit, locks, events, database
) -> None:
    """The invariant, at the one place every effect passes through.

    The mirror of the rule already enforced next to it: a state-changing tool
    that reports `not_applicable` is downgraded, because changing something
    without confirming it is not success. This is the other direction, and it is
    the one that let "I listed your windows" stand in for "I closed Edge".
    """
    from jarvis.core.tools.contract import ToolOutcome
    from jarvis.core.tools.invoker import ToolCall, ToolInvoker
    from jarvis.core.tools.ports import AutoApprovalPort
    from jarvis.core.permissions.models import Decision

    invoker = ToolInvoker(
        registry,
        permissions,
        audit,
        locks=locks,
        approvals=AutoApprovalPort(decision=Decision.ALLOW),
        event_bus=events,
        database=database,
    )
    registry.register(OverclaimingReadOnlyTool())
    try:
        result = invoker.invoke(ToolCall(tool_id="test.listing"))
    finally:
        invoker.shutdown(wait=False)

    # Asserted first, and deliberately. `denied` and `blocked` also carry
    # `not_applicable`, so without this the test passes on a call that never
    # ran — which is exactly how it passed the first time it was written.
    assert result.outcome is ToolOutcome.SUCCEEDED, (
        f"the tool did not run ({result.outcome}), so this proves nothing: "
        f"{result.message}"
    )
    assert result.verification is Verification.NOT_APPLICABLE, (
        "a tool that changes nothing reported that it verified something; "
        "the grounding layer reads that as licence to claim an action happened"
    )


# =========================================================================
# The reply that reached the owner
# =========================================================================
def test_listing_windows_does_not_license_claiming_a_close() -> None:
    """The 2026-08-06 transcript, reduced to its parts."""
    review = review_response(
        "The MS Edge window has been closed successfully.",
        tool_results=(_Result(Verification.NOT_APPLICABLE),),
    )

    assert review.amended, (
        "a reply claiming Edge was closed passed unchallenged on the strength "
        "of a window listing"
    )
    assert not review.verified_by_tool
    # The hedge keeps the original wording rather than deleting it, for the same
    # reason the untrusted boundary leaves a breakout attempt visible: the words
    # are the evidence of what went wrong. What must change is the front of the
    # reply, so the first thing the owner reads is that it did not happen.
    assert review.text.lower().startswith(("i could not", "i did not", "i have not")), (
        f"the reply still opens by claiming success: {review.text[:80]!r}"
    )


def test_the_past_passive_is_a_completion_claim_too() -> None:
    """The second escape, 2026-08-06 evening, verbatim.

    With the read-only fix in place the owner asked again, and this reached them
    unchallenged:

        "I see MS Edge (window reference: win-2a1c92ab) was closed successfully.
         There are now 3 windows open..."

    The audit shows `window.list` alone in that turn. So the licence was gone and
    the claim still got through, because the detector knew *"has been closed"*
    and *"is now closed"* and not *"was closed"* — and knew `successfully closed`
    but not `closed successfully`. Two spellings of the same sentence, one
    caught and one not.

    A closed list of phrases will always have a next gap; that is the nature of
    it. What makes this one worth closing rather than shrugging at is that the
    simple past passive is the most ordinary way in English to say a thing was
    done, so it was never an edge case.
    """
    review = review_response(
        "I see MS Edge (window reference: win-2a1c92ab) was closed successfully. "
        "There are now 3 windows open: Antigravity IDE, Brave and Project Jarvis.",
        tool_results=(_Result(Verification.NOT_APPLICABLE),),
    )

    assert review.amended, "'was closed successfully' passed as a listing"
    assert not review.verified_by_tool


def test_a_listing_that_merely_mentions_state_is_not_hedged() -> None:
    """The control, and the reason this widening is not simply "match more".

    Describing what is open is the honest use of a listing and the thing
    `window.list` is *for*. Hedging it would make the tool useless and teach the
    owner to read the hedge as noise, which is how a warning stops working.
    """
    for reply in (
        "You have three windows open: Antigravity IDE, Brave and Project Jarvis.",
        "MS Edge is not running at the moment.",
        "Nothing is open except File Explorer.",
    ):
        review = review_response(
            reply, tool_results=(_Result(Verification.NOT_APPLICABLE),)
        )
        assert not review.amended, f"an ordinary listing was hedged: {reply!r}"


def test_a_verified_close_may_still_be_reported_in_the_past_passive() -> None:
    """Widening the detector must not cost the true statement."""
    review = review_response(
        "MS Edge was closed successfully.",
        tool_results=(_Result(Verification.VERIFIED, tool_id="app.close"),),
    )

    assert not review.amended
    assert review.verified_by_tool


def test_a_read_only_result_is_still_labelled_as_coming_from_a_tool() -> None:
    """The other half, which must not be broken while fixing the first.

    A listing *is* an observation — real, and not a guess. It answers "what is
    open?" perfectly well. The distinction being drawn is only about whether it
    can support a claim that something was *done*.
    """
    review = review_response(
        "You have three windows open: Antigravity, WhatsApp and Project Jarvis.",
        tool_results=(_Result(Verification.NOT_APPLICABLE),),
    )

    assert review.label is SourceLabel.TOOL_RESULT
    assert not review.amended


def test_the_turn_tells_the_model_that_nothing_was_changed() -> None:
    """The other half of the 2026-08-06 failure.

    Grounding stops the false claim reaching the owner, which is the control
    that matters. But the model still had not closed anything, and it had to be
    told twice before it called the tool. Every individual tool message was
    accurate — a listing reported a listing — and none of them could say the
    thing that mattered, because *absence* is not something one result reports.
    """
    from jarvis.llm.conversation import _round_ledger

    ledger = _round_ledger([_Result(Verification.NOT_APPLICABLE)])

    assert "nothing on the computer has been changed" in ledger.lower()
    assert "do not describe the action as done" in ledger.lower()


def test_the_ledger_says_what_did_change_when_something_did() -> None:
    """It must not cry wolf: a real change has to be reportable as one."""
    from jarvis.llm.conversation import _round_ledger

    ledger = _round_ledger([_Result(Verification.VERIFIED, tool_id="app.close")])

    assert "app.close" in ledger
    assert "nothing on the computer has been changed" not in ledger.lower()


def test_a_real_close_still_supports_saying_it_closed() -> None:
    """The control. Making the false claim impossible must not make the true one
    impossible — `app.close` returning verified is exactly what a success claim
    is supposed to rest on."""
    review = review_response(
        "The MS Edge window has been closed successfully.",
        tool_results=(_Result(Verification.VERIFIED),),
    )

    assert not review.amended
    assert review.verified_by_tool
