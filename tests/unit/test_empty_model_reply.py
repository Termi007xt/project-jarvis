"""A model that returns nothing must not produce a blank, confident answer.

From a real session, twice in a row:

    You: what time is it right now?
    Jarvis:
    [from the local model]

The model returned an empty message, the screen rendered it faithfully, and the
source label made the nothing look deliberate. It is indistinguishable from
being ignored, and it is worse than an error because it carries a label.

The rule: if there are no words, say why there are no words. Never invent the
answer the model failed to give.
"""

from __future__ import annotations

import pytest

from jarvis.llm.conversation import ConversationEngine
from jarvis.llm.grounding import SourceLabel
from jarvis.llm.history import Conversation
from jarvis.llm.ports import ChatResponse
from jarvis.common import utc_now


class SilentProvider:
    """Answers every prompt with nothing at all."""

    available = True

    def __init__(self, text: str = "") -> None:
        self.text = text

    def unavailable_reason(self) -> str | None:
        return None

    def complete(self, messages, *, tools=(), **kwargs) -> ChatResponse:
        return ChatResponse(text=self.text, tool_calls=(), model="fake")


class NoopInvoker:
    def invoke(self, call):  # pragma: no cover - never reached here
        raise AssertionError("no tool should be invoked")


def _conversation() -> Conversation:
    return Conversation(
        conversation_id="c1", title="t", started_at=utc_now(), persisted=False
    )


def _engine(provider) -> ConversationEngine:
    return ConversationEngine(provider, NoopInvoker())


# -- the defect -------------------------------------------------------------
def test_an_empty_reply_becomes_an_explanation() -> None:
    turn = _engine(SilentProvider()).ask(_conversation(), "what time is it?")
    assert turn.ok
    assert turn.reply.strip(), "the reply was blank again"
    assert "empty" in turn.reply.lower()


@pytest.mark.parametrize("text", ["", "   ", "\n", "\t \n "])
def test_whitespace_only_counts_as_empty(text: str) -> None:
    turn = _engine(SilentProvider(text)).ask(_conversation(), "hello")
    assert turn.reply.strip()


def test_a_real_reply_is_left_exactly_as_it_is() -> None:
    turn = _engine(SilentProvider("It is four o'clock.")).ask(_conversation(), "time?")
    assert turn.reply == "It is four o'clock."


def test_the_explanation_does_not_claim_anything_was_done() -> None:
    """The substitute text must not itself trip FR-048."""
    turn = _engine(SilentProvider()).ask(_conversation(), "open brave")
    assert turn.label is SourceLabel.MODEL_ANSWER
    assert turn.review is not None and not turn.review.claims_success


def test_the_explanation_says_nothing_happened() -> None:
    turn = _engine(SilentProvider()).ask(_conversation(), "open brave")
    assert "nothing was done" in turn.reply.lower()


# -- with tool results ------------------------------------------------------
class _Result:
    def __init__(self, tool_id: str, message: str, succeeded: bool = True) -> None:
        self.tool_id = tool_id
        self.message = message
        self.succeeded = succeeded


def test_a_silent_model_after_a_successful_tool_reports_the_tool() -> None:
    """This is the "can you say my name out loud?" case: it worked, silently."""
    from jarvis.llm.conversation import _describe_silence

    text = _describe_silence((_Result("voice.speak", "Spoken aloud (1.2s)."),))
    assert "voice.speak" in text
    assert "Spoken aloud" in text
    assert "no words" in text


def test_a_silent_model_after_a_failed_tool_says_nothing_changed() -> None:
    from jarvis.llm.conversation import _describe_silence

    text = _describe_silence((_Result("app.open", "refused", succeeded=False),))
    assert "empty" in text.lower()
    assert "nothing was changed" in text.lower()


def test_a_silent_model_with_no_tools_asks_for_a_rephrase() -> None:
    from jarvis.llm.conversation import _describe_silence

    text = _describe_silence(())
    assert "rephrase" in text.lower()


def test_the_description_never_invents_an_answer() -> None:
    """It reports what ran. It must not guess what the model meant to say."""
    from jarvis.llm.conversation import _describe_silence

    for results in ((), (_Result("x", "y"),), (_Result("x", "y", False),)):
        text = _describe_silence(results)
        assert "probably" not in text.lower()
        assert "I think" not in text
