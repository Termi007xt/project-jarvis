"""A turn that ran out of steps still has to say what it did.

Reported from real use, 2026-08-05:

    Sir: move WhatsApp to the left half of the screen.
    Jarvis could not answer: stopped after 4 rounds of tool calls without
    reaching an answer. Nothing further was run (PRD FR-123).

    "it actually worked, but it reported and narrated fail."

The bound is right and stays — PRD FR-123 requires it, and an unbounded loop
between a model and a set of effects is exactly the failure it exists to
prevent. What was wrong is the report. `window.arrange` had run and succeeded;
the window really was on the left half. "Nothing further was run" is true about
the *plan* and reads as a failure of the *action*, which is the opposite of what
happened.

This matters more than a wording nit. The whole phase rests on Jarvis being
believed when it says something worked and when it says something did not, and a
turn that performs a state change and then reports failure spends that credit in
both directions at once: this time the user checked and found it done, and next
time they may not check the one that really did fail.
"""

from __future__ import annotations

from jarvis.llm.conversation import MAX_TOOL_ROUNDS, ConversationEngine
from jarvis.llm.ports import ChatResponse, ToolCallProposal


class AlwaysProposing:
    """A model that never stops asking for tools — the exhaustion case."""

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, messages, tools=None):
        self.calls += 1
        return ChatResponse(
            text="",
            tool_calls=(
                ToolCallProposal(tool_id="window.arrange", parameters={"window": "win-1"}),
            ),
        )


class SucceedingInvoker:
    """Every invocation works, and says so."""

    def __init__(self) -> None:
        self.invocations = 0

    def invoke(self, call, cancel_event=None):
        self.invocations += 1

        class _Result:
            succeeded = True
            tool_id = "window.arrange"
            outcome = "succeeded"
            verification = "verified"
            message = "'WhatsApp' is now at (0, 0, 1024, 1152)."
            failure_code = None
            output = {"verified": True}

        return _Result()


def _ask(question: str, invoker=None):
    """Run one turn, the way the shell does."""
    from datetime import datetime, timezone

    from jarvis.llm.history import Conversation

    engine = ConversationEngine(
        provider=AlwaysProposing(),
        invoker=invoker or SucceedingInvoker(),
    )
    conversation = Conversation(
        conversation_id="c1",
        title="t",
        started_at=datetime.now(timezone.utc),
        persisted=False,
    )
    return engine.ask(conversation, question)


def test_running_out_of_rounds_still_reports_the_actions_that_worked() -> None:
    """The defect, stated exactly."""
    turn = _ask("move WhatsApp to the left half of the screen")

    assert turn.error is not None, "the bound must still be reported"
    assert turn.tool_results, "the successful invocation was dropped from the turn"
    assert "WhatsApp" in turn.error or "window.arrange" in turn.error, (
        "the turn ran a state-changing action successfully and then reported "
        f"only that it gave up. What the owner saw: {turn.error!r}"
    )


def test_the_message_does_not_claim_nothing_happened_when_something_did() -> None:
    turn = _ask("move WhatsApp to the left half")

    assert not turn.error.lower().startswith("nothing"), (
        f"the report opens by denying the action that ran: {turn.error!r}"
    )
    # Eight identical lines is not eight facts. The model retrying the same
    # call is why the limit was reached; repeating its result once per attempt
    # buries the one thing the user needs to read.
    assert turn.error.count("window.arrange") == 1, (
        f"the same action is listed once per attempt: {turn.error!r}"
    )


def test_exhaustion_with_no_successful_action_still_says_so_plainly() -> None:
    """The control: when nothing ran, saying nothing ran is correct."""

    class RefusingInvoker:
        def invoke(self, call, cancel_event=None):
            class _Result:
                succeeded = False
                tool_id = "window.arrange"
                outcome = "failed"
                verification = "failed"
                message = "no such window"
                failure_code = "no_such_window"
                output = {}

            return _Result()

    turn = _ask("move something", invoker=RefusingInvoker())

    assert turn.error is not None
    assert "nothing" in turn.error.lower(), (
        "when no action succeeded, the report should say so"
    )


def test_the_bound_is_high_enough_for_an_ordinary_two_window_request() -> None:
    """"Put my IDE on the left and Settings on the right" is not exotic.

    It needs a listing, two arranges and a round in which the model finally
    answers. At four rounds that only fits if the model batches both arranges
    into one round, and it does not reliably — which is how a request that
    worked ended up reported as a failure.

    Raised rather than removed. FR-123 requires a bound; it does not require a
    bound so tight that ordinary multi-step requests hit it.
    """
    assert MAX_TOOL_ROUNDS >= 6, (
        f"MAX_TOOL_ROUNDS is {MAX_TOOL_ROUNDS}; a two-window arrange needs list "
        "+ arrange + arrange + answer, and any verification step on top of that "
        "exhausts it"
    )
