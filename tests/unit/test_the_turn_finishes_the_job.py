"""A turn does not end on a promise (FR-048, FR-123, ADR-0033).

Reported by the owner on 2026-08-06, third round on the same request:

    Sir: close MS edge
    Jarvis: I see there's a Microsoft Edge window open (win-d8a7c59e).
            I'll close it for you.          <- and then the turn ended
    Sir: did you close it?
    Jarvis: Nope, it's still there.          <- correct, and it could see that

The grounding checks were looking for the wrong shape. *"It has been closed"* is
a completion claim and *"I am closing it"* is an in-progress claim, and both are
caught. **"I'll close it for you" is neither** — it is a promise, which is not
false when it is said. It becomes false when the turn ends without keeping it.

And ending was the real fault. The loop stopped the moment the model produced
text instead of a tool call, so a model that announced an intention got exactly
what a model that finished the work got. The second exchange proves the model
*knew*: asked directly, it looked and said the window was still open. It had the
information and no reason to act on it, because nothing ever asked it to.

So an unbacked action claim now feeds back into the loop with the facts, rather
than ending the turn. Bounded, because unbounded loops are forbidden here and
because a model that cannot do something must be able to say so and stop.
"""

from __future__ import annotations

from jarvis.common import utc_now
from jarvis.core.tools.contract import Verification
from jarvis.llm.conversation import MAX_TOOL_ROUNDS, ConversationEngine
from jarvis.llm.grounding import claims_completion, promises_action
from jarvis.llm.history import Conversation
from jarvis.llm.ports import ChatResponse, ToolCallProposal


class ScriptedProvider:
    """Replies in a fixed order, so a turn's shape can be asserted exactly."""

    available = True

    def __init__(self, *replies) -> None:
        self.replies = list(replies)
        self.calls = 0

    def unavailable_reason(self) -> str | None:
        return None

    def complete(self, messages, *, tools=(), **kwargs) -> ChatResponse:
        self.calls += 1
        reply = self.replies[min(self.calls - 1, len(self.replies) - 1)]
        if isinstance(reply, str):
            return ChatResponse(text=reply, tool_calls=(), model="fake")
        return reply


class _Result:
    def __init__(self, tool_id, verification, succeeded=True) -> None:
        self.tool_id = tool_id
        self.verification = verification
        self.succeeded = succeeded
        self.outcome = "succeeded"
        self.message = f"{tool_id} ran"
        self.failure_code = None
        self.output = {}


class RecordingInvoker:
    """Runs whatever it is given and reports what the caller asked for."""

    def __init__(self, verification=Verification.VERIFIED) -> None:
        self.invoked: list[str] = []
        self._verification = verification

    def invoke(self, call):
        self.invoked.append(call.tool_id)
        return _Result(call.tool_id, self._verification)


def _conversation() -> Conversation:
    return Conversation(
        conversation_id="c1", title="t", started_at=utc_now(), persisted=False
    )


def _engine(provider, invoker):
    """An engine with the desktop-settle pause off.

    `SETTLE_SECONDS` exists so a real application has time to put its window up
    before the next step looks for it. Nothing here has a desktop, so paying it
    was seven seconds of the suite sleeping — which the owner noticed as the
    suite being heavy, and they were right.
    """
    return ConversationEngine(provider, invoker, settle_seconds=0.0)


def _proposal(tool_id: str) -> ChatResponse:
    return ChatResponse(
        text="",
        tool_calls=(ToolCallProposal(tool_id=tool_id, parameters={}),),
        model="fake",
    )


# =========================================================================
# A promise is its own shape
# =========================================================================
def test_a_promise_is_recognised_as_an_unkept_action() -> None:
    assert promises_action("I'll close it for you.")
    assert promises_action("Let me close that window.")
    assert promises_action("I'm going to open Brave now.")
    assert promises_action("I will close MS Edge.")


def test_a_promise_is_not_a_completion_claim() -> None:
    """They are different failures and must stay distinguishable.

    A completion claim is false the moment it is said. A promise is true when
    said and becomes false only if the turn ends without keeping it — which is
    why the answer to one is a rewrite and the answer to the other is to carry
    on working.
    """
    assert not claims_completion("I'll close it for you.")


def test_an_offer_is_not_a_promise() -> None:
    """Offering to act is the one thing Jarvis is supposed to do before acting.

    "Want me to close it properly?" came from the same transcript, and treating
    it as an unkept promise would make Jarvis act on a question it had asked but
    the owner had not yet answered — which is worse than the bug being fixed.
    """
    assert not promises_action("Want me to close it properly?")
    assert not promises_action("Would you like me to close it for you?")
    assert not promises_action("Shall I close MS Edge?")


# =========================================================================
# The turn carries on
# =========================================================================
def test_the_turn_continues_after_a_promise_instead_of_ending() -> None:
    """The whole point. The model said it would; the turn makes it."""
    provider = ScriptedProvider(
        "I see a Microsoft Edge window open. I'll close it for you.",
        _proposal("app.close"),
        "Done, Sir. The Microsoft Edge window is closed.",
    )
    invoker = RecordingInvoker()

    turn = _engine(provider, invoker).ask(_conversation(), "close MS Edge")

    assert "app.close" in invoker.invoked, (
        "the turn ended on 'I'll close it for you' without closing anything"
    )
    assert turn.ok


def test_a_claim_with_nothing_behind_it_is_also_pushed_back() -> None:
    """"Done, Sir" with no tool is the same failure wearing the other tense."""
    provider = ScriptedProvider(
        "Done, Sir. The Microsoft Edge window is closed and verified.",
        _proposal("app.close"),
        "Closed.",
    )
    invoker = RecordingInvoker()

    _engine(provider, invoker).ask(_conversation(), "close MS Edge")

    assert "app.close" in invoker.invoked


def test_a_verified_open_does_not_license_a_claim_about_playing() -> None:
    """Reported by the owner on 2026-08-06, and the sharpest of the three.

        Sir: open YouTube music and play whatever song is in the queue.
        Jarvis: YouTube Music is now open and playing the current song, Sir.

    The audit shows one tool in that turn: `app.open`, verified. The song never
    played. Asking "did any tool verify something?" cannot catch this, because
    one did — opening the application really had happened. What was false was
    the claim about *playing*, and nothing that can play anything ever ran.

    So a claim is checked against the tools that could have produced it. It is
    the same failure as a listing licensing a close, one step further along:
    there, the tool proved nothing; here, it proved the wrong thing.
    """
    from jarvis.llm.grounding import unbacked_claims

    opened = _Result("app.open", Verification.VERIFIED)

    unbacked = unbacked_claims(
        "YouTube Music is now open and playing the current song from the queue, Sir.",
        (opened,),
    )

    assert "playing" in unbacked, "a verified app.open carried a claim about playback"
    assert "opened" not in unbacked, "opening it really did happen and must stand"


def test_the_turn_carries_on_until_the_song_is_actually_played() -> None:
    """The same case, end to end: it must not stop after opening."""
    provider = ScriptedProvider(
        _proposal("app.open"),
        "YouTube Music is now open and playing the current song from the queue.",
        _proposal("media.control"),
        "Playing now, Sir.",
    )
    invoker = RecordingInvoker()

    _engine(provider, invoker).ask(
        _conversation(), "open YouTube Music and play whatever is in the queue"
    )

    assert invoker.invoked == ["app.open", "media.control"], (
        f"the turn stopped after opening: {invoker.invoked}"
    )


def test_an_unrecognised_tool_is_never_contradicted() -> None:
    """The mapping is a closed list, so it must not conclude from ignorance.

    A verified tool this mapping has never heard of might be exactly the one
    that did the thing. "I cannot tell" has to mean silence, or every tool added
    later starts hedging true replies — which is how a warning stops being read.
    """
    from jarvis.llm.grounding import unbacked_claims

    future = _Result("media.something_new", Verification.VERIFIED)

    assert unbacked_claims("The song is now playing.", (future,)) == ()


# =========================================================================
# A failure nobody dealt with
# =========================================================================
class _Failure:
    def __init__(self, tool_id, outcome="failed", message="it did not work") -> None:
        self.tool_id = tool_id
        self.outcome = outcome
        self.succeeded = False
        self.verification = Verification.FAILED
        self.message = message
        self.failure_code = "some_failure"
        self.output = None


class FailThenSucceed:
    """Fails the first call to a tool and succeeds afterwards."""

    def __init__(self, failing: str, message: str) -> None:
        self.invoked: list[str] = []
        self._failing = failing
        self._message = message

    def invoke(self, call):
        self.invoked.append(call.tool_id)
        if call.tool_id == self._failing and self.invoked.count(self._failing) == 1:
            return _Failure(call.tool_id, message=self._message)
        return _Result(call.tool_id, Verification.VERIFIED)


def test_a_failed_tool_does_not_end_the_turn() -> None:
    """The owner's YouTube Music session, from the audit log.

        17:02:35  youtube.play  failed  "Brave is already open, and a browser
                                         that is already running cannot..."
        -- turn ended; Jarvis said "I need to restart the browser first"

    The failure named its own remedy and the model said the right next step out
    loud. It stopped because stopping was allowed. This is the strongest signal
    available and the only one that needs no guess about English: a tool failed,
    nothing put it right, so the request has not been carried out.
    """
    provider = ScriptedProvider(
        _proposal("youtube.play"),
        "The youtube.play tool failed because Brave is already open. I need to "
        "restart the browser first using browser.restart, then try again.",
        _proposal("browser.restart"),
        _proposal("youtube.play"),
        "Playing now, Sir.",
    )
    invoker = FailThenSucceed("youtube.play", "Brave is already open")

    _engine(provider, invoker).ask(
        _conversation(), "play whatever is in the queue"
    )

    assert invoker.invoked == ["youtube.play", "browser.restart", "youtube.play"], (
        f"the turn stopped on a failure it could have worked past: {invoker.invoked}"
    )


def test_a_refused_permission_is_never_retried() -> None:
    """`denied` is the user saying no, and nagging is worse than the bug.

    A turn that retried a refusal would re-ask for approval until the follow-ups
    ran out. That is one of the three ways this whole mechanism can go wrong,
    and it is the one that would make Jarvis unpleasant to live with.
    """
    denied = _Failure("app.close", outcome="denied", message="you said no")

    class Denier:
        def __init__(self) -> None:
            self.invoked: list[str] = []

        def invoke(self, call):
            self.invoked.append(call.tool_id)
            return denied

    provider = ScriptedProvider(
        _proposal("app.close"),
        "I could not close it — you did not approve that.",
    )
    invoker = Denier()

    _engine(provider, invoker).ask(_conversation(), "close MS Edge")

    assert invoker.invoked == ["app.close"], (
        f"a refusal was retried: {invoker.invoked}"
    )


def test_an_empty_reply_after_tools_carries_on_instead_of_explaining_itself() -> None:
    """The owner heard the diagnostic read aloud.

        Jarvis: "That went through, but the model returned no words to go with
                 it. Here is what actually ran — window.list: 6 window(s) open;
                 window.list: 6 window(s) open."

    An empty reply is not an answer. If tools ran there is something to say
    about them, and the turn should ask for it rather than narrate its own
    plumbing at the user.
    """
    provider = ScriptedProvider(
        _proposal("window.list"),
        "",
        "There are six windows open, Sir.",
    )

    turn = _engine(provider, RecordingInvoker()).ask(
        _conversation(), "what is open?"
    )

    assert turn.reply == "There are six windows open, Sir."
    assert "returned no words" not in turn.reply


def test_narration_the_old_patterns_missed_now_carries_on() -> None:
    """Three real stalls, none of which matched a known action verb.

    "I'll **use** app.close", "I **need to** restart the browser first", "**Let
    me proceed** with that". Extending the verb list a fourth time would have
    been the third patch to the same guess; this is a loose net for intent of
    any kind, and it is loose because it only decides whether to keep working.
    """
    from jarvis.llm.conversation import _states_an_intention

    assert _states_an_intention("I'll use app.close to close it.")
    assert _states_an_intention("I need to restart the browser first.")
    assert _states_an_intention("Let me proceed with that.")
    assert _states_an_intention("Now I need to open YouTube Music.")
    # An offer is still a question awaiting an answer, not a stalled task.
    assert not _states_an_intention("Would you like me to close it?")


def test_a_model_that_only_ever_promises_still_stops() -> None:
    """FR-123. "Keep going until it is done" cannot become "keep going".

    A model that cannot do the thing must be able to fail, and a loop that only
    exits on success is a hang wearing a helpful expression.
    """
    provider = ScriptedProvider("I'll close it for you.")  # forever
    invoker = RecordingInvoker()

    turn = _engine(provider, invoker).ask(_conversation(), "close MS Edge")

    assert provider.calls < 40, f"the turn did not stop: {provider.calls} model calls"
    assert turn.reply.strip(), "it gave up without saying anything"
    assert not invoker.invoked


def test_the_last_word_is_honest_when_it_never_managed_it() -> None:
    """After the pushing stops, the reply must not still be a promise."""
    provider = ScriptedProvider("I'll close it for you.")
    turn = _engine(provider, RecordingInvoker()).ask(
        _conversation(), "close MS Edge"
    )

    assert turn.review is not None and turn.review.amended, (
        f"the owner was left with an unkept promise: {turn.reply!r}"
    )


def test_a_finished_answer_is_not_pushed_back() -> None:
    """The control, and the one that keeps this from being a nuisance.

    A turn that did the work and says so must end immediately. Nudging it would
    double every successful turn's cost and eventually talk it out of a correct
    answer.
    """
    provider = ScriptedProvider(
        _proposal("app.close"),
        "Done, Sir. The Microsoft Edge window is closed.",
    )
    invoker = RecordingInvoker(verification=Verification.VERIFIED)

    turn = _engine(provider, invoker).ask(_conversation(), "close MS Edge")

    assert provider.calls == 2, f"a completed turn was pushed back ({provider.calls})"
    assert turn.ok


def test_an_ordinary_answer_is_not_pushed_back() -> None:
    """Conversation is not a task. "What's good bro?" must cost one call."""
    provider = ScriptedProvider("Not much, just here and ready to help.")

    turn = _engine(provider, RecordingInvoker()).ask(
        _conversation(), "what's good bro?"
    )

    assert provider.calls == 1
    assert turn.ok


def test_progress_resets_the_budget_so_a_long_task_is_not_cut_off() -> None:
    """Reported by the owner on 2026-08-06, on a three-part request.

    The turn spent its follow-ups working through the first part and then ended
    mid-sentence on the second:

        "The browser restart didn't work properly. Let me try a different
         approach - I'll use the media control tool directly:"

    The right next step, named and never taken, because the budget had run out
    three steps earlier. Counting *total* pushes punishes a task for being long;
    what matters is whether the turn is stuck, and a turn that has completed
    something since the last push plainly is not.

    `MAX_TOOL_ROUNDS` is still the hard bound, so this cannot run away.
    """
    provider = ScriptedProvider(
        "I'll open it for you.",            # push 1
        _proposal("app.open"),              # progress
        "Now I need to search for it.",     # push 2 — budget should have reset
        _proposal("youtube.search"),        # progress
        "Let me play it now.",              # push 3 — reset again
        _proposal("youtube.play"),          # progress
        "Playing now, Sir.",
    )
    invoker = RecordingInvoker()

    _engine(provider, invoker).ask(
        _conversation(), "open YouTube and play something"
    )

    assert invoker.invoked == ["app.open", "youtube.search", "youtube.play"], (
        f"the turn was cut off while it was still making progress: {invoker.invoked}"
    )


def test_a_stall_with_no_progress_still_stops() -> None:
    """The other half. Resetting on progress must not remove the bound."""
    provider = ScriptedProvider("I'll close it for you.")  # forever, no tools
    invoker = RecordingInvoker()

    _engine(provider, invoker).ask(_conversation(), "close MS Edge")

    assert provider.calls <= MAX_TOOL_ROUNDS, (
        f"an unproductive turn ran past its bound: {provider.calls}"
    )
