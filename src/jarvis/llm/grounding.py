"""Where an answer came from, and what counts as done (PRD FR-047, FR-048).

Two separate honesty rules live here because they are easy to conflate:

**FR-047 — source labelling.** Every claim Jarvis makes is one of five things:
the model's own answer, a retrieved fact, an inference, a tool result, or an
admission of uncertainty. A model answer stated as though it were a tool result
is the specific failure this exists to prevent.

**FR-048 — tool-grounded success.** A conversational reply may only say an
action succeeded when a tool actually verified it. ``succeeded`` plus
``unverified`` is not success (PRD AT-018); it is a tool that ran and could not
confirm its effect, and the reply has to say so.

Neither rule can be enforced by asking the model nicely. Both are enforced here,
on the way out, against the tool results the invoker actually produced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

__all__ = [
    "SourceLabel",
    "GroundedClaim",
    "GroundingReview",
    "review_response",
    "claims_completion",
    "claims_in_progress",
    "SUCCESS_PHRASES",
    "IN_PROGRESS_PHRASES",
]


class SourceLabel(str, Enum):
    """PRD FR-047's five categories, and nothing outside them."""

    MODEL_ANSWER = "model_answer"
    RETRIEVED_FACT = "retrieved_fact"
    INFERENCE = "inference"
    TOOL_RESULT = "tool_result"
    UNCERTAINTY = "uncertainty"

    @property
    def display(self) -> str:
        return {
            SourceLabel.MODEL_ANSWER: "from the local model",
            SourceLabel.RETRIEVED_FACT: "from a retrieved fact",
            SourceLabel.INFERENCE: "inferred",
            SourceLabel.TOOL_RESULT: "confirmed by a tool",
            SourceLabel.UNCERTAINTY: "uncertain",
        }[self]


#: Phrases that assert an action was completed. Deliberately conservative: a
#: false positive costs a hedged sentence, a false negative lets Jarvis claim a
#: success it never verified.
#: Things an action leaves behind. Shared by the perfect and simple-past forms
#: below, because "has been closed" and "was closed" are the same claim.
_DONE_TO_IT = (
    "opened|launched|started|closed|sent|deleted|created|saved|played|"
    "moved|resized|minimised|minimized|maximised|maximized|captured|arranged"
)

SUCCESS_PHRASES: tuple[str, ...] = (
    r"\bi(?:'ve| have)? (?:opened|launched|started|closed|sent|deleted|created|saved|played)\b",
    r"\bis now (?:open|running|playing|closed|paused|muted)\b",
    rf"\bhas been (?:{_DONE_TO_IT})\b",
    # The simple past passive, added 2026-08-06 after it reached the owner
    # twice. "I see MS Edge was closed successfully" is the same assertion as
    # "MS Edge has been closed", and only the second was being caught — two
    # spellings of one sentence, one hedged and one not. It is also the most
    # ordinary way in English to say a thing was done, so it was never an edge
    # case; it was the main case, missed.
    #
    # Deliberately *not* here: the bare present state, "MS Edge is closed".
    # That is what a listing legitimately reports, and hedging Jarvis's answer
    # to "what's open?" would make the reading tools useless and teach the owner
    # to skip the hedge — which is how a warning stops working.
    rf"\b(?:was|were) (?:{_DONE_TO_IT})\b",
    # "Done." as a whole statement, not the word "done" inside a sentence such
    # as "the wrong thing to have done". Anchored to a sentence boundary, since
    # the bare word is far too common to treat as a completion claim.
    r"(?:^|[.!?]\s+|\n)(?:done|all set|that'?s done|completed successfully)\b[.!\s]*$",
    # Both orders. `successfully closed` was covered and `closed successfully`
    # was not, which is the other half of the same escape.
    r"\bsuccessfully \w+ed\b",
    r"\b\w+ed successfully\b",
)

_SUCCESS_PATTERN = re.compile("|".join(SUCCESS_PHRASES), re.IGNORECASE | re.MULTILINE)

#: Verbs Jarvis might narrate itself performing. A closed list, because the
#: point is to catch a specific dishonest shape, not to police prose.
_ACTION_VERBS = (
    "search|open|play|launch|start|close|download|send|creat|delet|sav|"
    "look|check|run|navigat|type|click"
)

#: Phrases that assert an action is **under way**, as opposed to finished.
#:
#: Jarvis never has anything under way at the moment it speaks. `ConversationEngine.ask`
#: runs every tool to completion and only then produces a reply, so by the time
#: a sentence reaches the user every action it could describe has already
#: finished or never started. That makes the present progressive false in both
#: directions, which is why these need no notion of what actually ran.
#:
#: Both real examples are from 2026-08-05: *"Now searching for 'best monitors'"*
#: — said while `app.open` sat there genuinely verified and no search tool had
#: been called at all — and *"Searching YouTube for latest anime now, Sir..."*,
#: said with no tool call behind it whatsoever.
IN_PROGRESS_PHRASES: tuple[str, ...] = (
    # First person: "I'm searching", "I am now opening". Unambiguous without
    # any other marker, because only Jarvis is the subject.
    rf"\bi(?:'m| am)\s+(?:just\s+|now\s+)?(?:{_ACTION_VERBS})\w*ing\b",
    # Sentence-initial gerund, but only with "now": "Now searching for X",
    # "Opening a session now". The marker is what separates a narrated action
    # from a gerund used as a subject — "Searching YouTube requires the browser
    # to be open" is a statement of fact and must not be hedged.
    rf"(?:^|[.!?]\s+|\n)\s*(?:now\s+)?(?:{_ACTION_VERBS})\w*ing\b[^.!?\n]*\bnow\b",
    rf"(?:^|[.!?]\s+|\n)\s*now\s+(?:{_ACTION_VERBS})\w*ing\b",
)

#: Phrases that promise an action rather than reporting one.
#:
#: A third shape, and the one that ended a turn on 2026-08-06: *"I'll close it
#: for you."* It is not a completion claim — nothing is claimed done — and not
#: an in-progress claim either. It is **true when it is said**, and becomes
#: false only if the turn ends without keeping it.
#:
#: That is why the answer to this one is different. A completion claim is
#: rewritten, because it was false the moment it was made. A promise is fed back
#: into the loop so the model can keep it, and only rewritten if it never does.
#:
#: Questions are excluded by `promises_action`, sentence by sentence. *"Want me
#: to close it properly?"* is from the same transcript, and acting on it would
#: mean answering a question the owner had not yet answered.
PROMISE_PHRASES: tuple[str, ...] = (
    rf"\bi(?:'ll| will)\s+(?:now\s+|just\s+|go\s+ahead\s+and\s+)?(?:{_ACTION_VERBS})\w*\b",
    rf"\b(?:let me|i'm going to|i am going to)\s+(?:just\s+|now\s+)?(?:{_ACTION_VERBS})\w*\b",
)

_PROMISE_PATTERN = re.compile("|".join(PROMISE_PHRASES), re.IGNORECASE | re.MULTILINE)

#: Which tools could actually have performed a claimed action.
#:
#: Added 2026-08-06 after this, with `app.open` genuinely verified and no other
#: tool called at all:
#:
#:     Sir: open YouTube Music and play whatever song is in the queue.
#:     Jarvis: YouTube Music is now open and playing the current song, Sir.
#:
#: The song never played. Asking "did *any* tool verify something?" cannot catch
#: that, because one did: opening the application really had happened. The claim
#: that was false was about *playing*, and nothing that could play anything ever
#: ran. The same shape had already appeared as a listing licensing a close.
#:
#: So a claim is now checked against tools that could have produced it. A closed
#: mapping rather than anything clever: it is exactly as good as its entries,
#: which is a limit worth having in the open rather than a general mechanism
#: that is subtly wrong.
CLAIM_EVIDENCE: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "closed",
        (r"\b(?:has been|have been|was|were|is now|are now)\s+clos(?:ed)?\b",
         r"\bi(?:'ve| have)?\s*closed\b"),
        ("app.close", "app.force_close"),
    ),
    (
        "opened",
        (r"\b(?:has been|have been|was|were|is now|are now)\s+open(?:ed)?\b",
         r"\bi(?:'ve| have)?\s*(?:opened|launched|started)\b"),
        ("app.open", "web.open_url", "browser.restart", "youtube.search"),
    ),
    (
        "playing",
        (r"\b(?:is|are)\s+now\s+[^.!?]*\bplaying\b",
         r"\b(?:has|have)\s+(?:been\s+)?[^.!?]*\bplay(?:ed|ing)\b",
         r"\bi(?:'ve| have)?\s*played\b",
         r"\b(?:started|resumed)\s+playing\b"),
        ("media.control", "youtube.play"),
    ),
    (
        "searched",
        (r"\b(?:has been|have been|was|were)\s+searched\b",
         r"\bi(?:'ve| have)?\s*searched\b"),
        ("web.search", "youtube.search"),
    ),
    (
        "captured",
        (r"\b(?:has been|have been|was|were)\s+(?:captured|screenshotted)\b",
         r"\bi(?:'ve| have)?\s*(?:captured|taken a screenshot)\b"),
        ("screen.capture",),
    ),
    (
        "arranged",
        (r"\b(?:has been|have been|was|were|is now|are now)\s+"
         r"(?:moved|resized|minimised|minimized|maximised|maximized|snapped)\b",
         r"\bi(?:'ve| have)?\s*(?:moved|resized|minimised|minimized|maximised|maximized)\b"),
        ("window.arrange",),
    ),
)

_CLAIM_PATTERNS: tuple[tuple[str, "re.Pattern[str]", tuple[str, ...]], ...] = tuple(
    (action, re.compile("|".join(phrases), re.IGNORECASE | re.MULTILINE), tools)
    for action, phrases, tools in CLAIM_EVIDENCE
)

#: Every tool this mapping knows the purpose of. Used to tell "that tool cannot
#: have done this" from "I have no idea what that tool does", which are very
#: different and only the first of them justifies contradicting the model.
_KNOWN_TOOLS: frozenset[str] = frozenset(
    tool for _, _, tools in CLAIM_EVIDENCE for tool in tools
)


def promises_action(text: str) -> bool:
    """Whether a reply undertakes to do something rather than reporting it."""
    for sentence in re.split(r"(?<=[.!?\n])\s+", text or ""):
        if sentence.rstrip().endswith("?"):
            continue
        if _PROMISE_PATTERN.search(sentence):
            return True
    return False


def unbacked_claims(text: str, tool_results: tuple[object, ...]) -> tuple[str, ...]:
    """Actions the reply claims that no tool capable of them ever verified.

    "Any tool verified something" is too weak a test, and both of the failures
    that produced this mapping proved it in different directions: a *listing*
    licensed a close, and a verified *open* licensed a playback that never
    happened. The question has to be whether the thing that was claimed is the
    thing some tool actually did.
    """
    verified_tools = {
        str(getattr(result, "tool_id", ""))
        for result in tool_results
        if getattr(result, "succeeded", False)
        and str(getattr(getattr(result, "verification", None), "value", "")) == "verified"
    }
    if not verified_tools:
        # Nothing was confirmed at all. That is the plain unverified-success
        # case, which the caller already handles; saying it twice here would
        # hedge the same sentence for two different reasons.
        return ()

    # Only conclude from tools this mapping actually understands. A verified
    # tool that is not listed anywhere here might be exactly the one that did
    # the thing — the mapping is a closed list and closed lists are incomplete
    # by construction, so an unrecognised tool means "cannot tell", never
    # "did not happen". Being wrong in that direction would hedge true replies,
    # which is how a warning stops being read.
    if not verified_tools.issubset(_KNOWN_TOOLS):
        return ()

    return tuple(
        action
        for action, pattern, tools in _CLAIM_PATTERNS
        if pattern.search(text or "") and not verified_tools.intersection(tools)
    )


_IN_PROGRESS_PATTERN = re.compile(
    "|".join(IN_PROGRESS_PHRASES), re.IGNORECASE | re.MULTILINE
)


@dataclass(frozen=True)
class GroundedClaim:
    """One statement and the label that must accompany it."""

    text: str
    label: SourceLabel
    evidence: str | None = None

    def render(self) -> str:
        if self.label is SourceLabel.MODEL_ANSWER:
            return self.text
        return f"{self.text} ({self.label.display})"


@dataclass(frozen=True)
class GroundingReview:
    """The verdict on a proposed reply."""

    text: str
    label: SourceLabel
    claims_success: bool
    verified_by_tool: bool
    amended: bool
    note: str | None = None

    @property
    def honest(self) -> bool:
        """True when nothing in the reply overstates what actually happened."""
        return not self.claims_success or self.verified_by_tool


def claims_completion(text: str) -> bool:
    """Whether a reply asserts that something was done, or is being done."""
    return bool(_SUCCESS_PATTERN.search(text or "")) or claims_in_progress(text)


def claims_in_progress(text: str) -> bool:
    """Whether a reply asserts an action is under way right now.

    Questions are excluded sentence by sentence. *"Would you like me to start
    searching now?"* offers to act and must stay an offer; hedging Jarvis's
    questions would make it unusable to talk to, and offering is the one thing
    it is supposed to do before acting.
    """
    for sentence in re.split(r"(?<=[.!?\n])\s+", text or ""):
        if sentence.rstrip().endswith("?"):
            continue
        if _IN_PROGRESS_PATTERN.search(sentence):
            return True
    return False


def _verification_of(result: object) -> str:
    """The verification value of a succeeded result; empty if it did not succeed."""
    if not getattr(result, "succeeded", False):
        return ""
    return str(getattr(getattr(result, "verification", None), "value", ""))


def review_response(
    text: str,
    *,
    tool_results: tuple[object, ...] = (),
    retrieved: bool = False,
    uncertain: bool = False,
) -> GroundingReview:
    """Label a reply and stop it claiming an unverified success.

    ``tool_results`` are ``ToolResult`` objects from the invoker. Two different
    questions are asked of them, and conflating the two is the mistake this
    function exists to avoid:

    * **What is the source?** A succeeded read-only tool reports
      ``not_applicable`` — nothing changed, so there was nothing to verify — and
      what it returned is still a real observation, not a guess. It counts as a
      tool result for FR-047 labelling.
    * **May the reply claim an action happened?** Only a ``verified`` result
      supports that. A read-only tool cannot confirm that anything was done, so
      ``not_applicable`` never licenses a success claim (FR-048, AT-018).
    """
    verified = any(_verification_of(result) == "verified" for result in tool_results)
    observed = any(
        _verification_of(result) in ("verified", "not_applicable") for result in tool_results
    )
    ran_a_tool = bool(tool_results)

    if uncertain:
        label = SourceLabel.UNCERTAINTY
    elif observed:
        label = SourceLabel.TOOL_RESULT
    elif retrieved:
        label = SourceLabel.RETRIEVED_FACT
    elif ran_a_tool:
        # A state-changing tool ran and could not confirm its effect. That is
        # not a tool result in the FR-047 sense; it is at best an inference.
        label = SourceLabel.INFERENCE
    else:
        label = SourceLabel.MODEL_ANSWER

    # Checked before the verified/unverified question, because no tool result
    # can support it either way. A completed tool call is evidence about the
    # past; "I am now searching" is a claim about the present, and Jarvis has
    # nothing in flight at the moment it speaks. On 2026-08-05 this reached the
    # owner as "Now searching for 'best monitors'" beside a genuinely verified
    # `app.open`, labelled "confirmed by a tool" — so asking whether any tool
    # verified anything could never have caught it.
    if claims_in_progress(text):
        return GroundingReview(
            text=_hedge_in_progress(text),
            label=label,
            claims_success=True,
            verified_by_tool=False,
            amended=True,
            note=(
                "the reply described an action as under way. Nothing is ever in "
                "flight when Jarvis speaks — a turn finishes its tools first — so "
                "this was rewritten to say what actually ran (PRD FR-047, FR-048)."
            ),
        )

    # A claim about the wrong thing. `verified` alone asks whether *any* tool
    # confirmed *something*, which was true when a verified `app.open` carried
    # "and playing the current song" — nothing that could play anything had run.
    unbacked = unbacked_claims(text, tool_results)

    # An unkept promise, checked after the two claim shapes because it is the
    # weakest of the three: it was true when it was said. By the time a reply
    # reaches the user the turn has already pushed back on it as far as it is
    # allowed to (ADR-0033), so a promise still standing here is one the model
    # was given several chances to keep and did not.
    if promises_action(text) and (not verified or unbacked):
        return GroundingReview(
            text=_hedge_promise(text),
            label=label,
            claims_success=True,
            verified_by_tool=False,
            amended=True,
            note=(
                "the reply undertook to do something and the turn ended without "
                "it being done. Rewritten so the last word is not an intention "
                "(PRD FR-048)."
            ),
        )

    asserts_success = claims_completion(text) or bool(unbacked)
    if asserts_success and (not verified or unbacked):
        amended = _hedge(text, ran_a_tool)
        return GroundingReview(
            text=amended,
            label=label,
            claims_success=True,
            verified_by_tool=False,
            amended=True,
            note=(
                "the reply claimed an action was completed, but no tool verified "
                "it. Rewritten to say what is actually known (PRD FR-048, AT-018)."
            ),
        )

    return GroundingReview(
        text=text,
        label=label,
        claims_success=asserts_success,
        verified_by_tool=verified,
        amended=False,
    )


def _hedge_promise(text: str) -> str:
    """Say the promise was not kept, and keep the words that made it.

    The original stays for the same reason it does everywhere else here: the
    wording is the evidence of what went wrong, and a reply that quietly
    replaced it would make the next occurrence harder to see.
    """
    return (
        "I did not do that, and I am not going to do it after this message — a "
        "turn finishes its work before it answers. Here is what I was about to "
        f"say, which promised something that did not happen: {text.strip()}"
    )


def _hedge_in_progress(text: str) -> str:
    """Say plainly that nothing is happening, and keep the words that claimed it.

    The original is kept rather than discarded, for the same reason the untrusted
    boundary leaves a breakout attempt visible: the wording is the evidence of
    what went wrong, and hiding it would make the next occurrence harder to see.
    """
    return (
        "That is not under way — I finish everything before I answer, so nothing "
        "is running in the background. Here is what I was going to say, which "
        f"describes something that had not started: {text.strip()}"
    )


def _hedge(text: str, ran_a_tool: bool) -> str:
    """Replace an unverified success claim with what is actually known."""
    if ran_a_tool:
        return (
            "I could not confirm that, so I am not going to say it worked. "
            "The action ran but its effect could not be verified. "
            f"What I was going to say was: {text.strip()}"
        )
    return (
        "I have not actually done that — no tool ran, so nothing changed on "
        f"your computer. What I can tell you is: {text.strip()}"
    )
