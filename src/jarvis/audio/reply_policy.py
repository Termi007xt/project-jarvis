"""When a spoken request deserves a spoken answer (PRD FR-030, FR-048).

Answering every spoken request out loud sounds attentive for about a day. Then
"open Brave" starts costing four seconds of narration about a window that is
already on the screen, and the useful sentences get lost among the courteous
ones.

The distinction that matters is not whether a tool ran — "what's the volume?"
runs a tool and still deserves an answer — but whether the user asked for
*information* or gave an *instruction*. An instruction that succeeded is
self-evidencing, so it gets a two-tone cue and nothing else. Three things
always override that, because being quiet about them is a failure rather than a
courtesy: something went wrong, a tool did not succeed, or Jarvis needs an
answer before it can carry on.

Decided here, in code, rather than asked of the model. A model deciding whether
to speak drifts, and the drift is invisible: nobody notices the sentence that
was not said.
"""

from __future__ import annotations

from enum import Enum
from typing import Sequence

__all__ = ["ReplyVoice", "SpeakReplies", "should_speak", "QUESTION_OPENERS"]


class SpeakReplies(str, Enum):
    """The user-facing setting, ``audio.speak_replies``."""

    ALWAYS = "always"
    WHEN_USEFUL = "when_useful"
    NEVER = "never"


class ReplyVoice(str, Enum):
    """What the shell should do with a finished reply."""

    #: Say it out loud.
    SPEAK = "speak"
    #: Play the "done" cue. The reply is on the Conversation screen either way.
    CUE = "cue"
    #: Make no sound at all.
    SILENT = "silent"


#: First words that make an utterance a request for information rather than an
#: instruction. Deliberately generous: mistaking a command for a question costs
#: one unnecessary sentence, mistaking a question for a command costs the
#: answer entirely.
QUESTION_OPENERS: frozenset[str] = frozenset(
    {
        "what", "whats", "when", "where", "who", "whom", "whose", "why", "how",
        "which", "is", "are", "am", "was", "were", "do", "does", "did", "can",
        "could", "will", "would", "should", "shall", "may", "might", "have",
        "has", "had", "tell", "explain", "describe", "list", "show", "read",
        "any", "anything",
    }
)


def _asks_something(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if "?" in stripped:
        return True
    first = stripped.split()[0].strip("\"'`.,;:!-").casefold()
    return first in QUESTION_OPENERS


def should_speak(
    *,
    spoken_request: bool,
    policy: str,
    request: str,
    reply: str,
    tool_results: Sequence[object],
    ok: bool,
) -> ReplyVoice:
    """Decide how a finished turn should sound.

    ``spoken_request`` is the whole reason this is not simply a setting: a
    typed request is answered on the screen the user is already looking at, and
    talking over it is an interruption, not a service.
    """
    if not spoken_request:
        return ReplyVoice.SILENT
    if policy == SpeakReplies.NEVER:
        return ReplyVoice.SILENT

    # A failure the user cannot see is a failure they will not know about,
    # because a spoken request does not raise the window.
    if not ok:
        return ReplyVoice.SPEAK
    if not reply.strip():
        return ReplyVoice.CUE
    if policy == SpeakReplies.ALWAYS:
        return ReplyVoice.SPEAK
    if policy != SpeakReplies.WHEN_USEFUL:
        # An unrecognised setting must not quietly make Jarvis mute.
        return ReplyVoice.SPEAK

    if any(not getattr(result, "succeeded", False) for result in tool_results):
        return ReplyVoice.SPEAK
    if _asks_something(request):
        return ReplyVoice.SPEAK
    # An instruction whose tools all succeeded, checked *before* the reply is
    # read for questions. The model is fond of closing a finished action with an
    # offer — "opened it. Want me to check system status, or open Brave
    # directly?" — and a question mark used to be enough to turn a
    # self-evidencing action into four seconds of narration about a window
    # already on the screen. Whether the model felt conversational is not a fact
    # about what the user asked for, so it does not get to overrule it.
    if tool_results:
        return ReplyVoice.CUE
    # Nothing ran, so a reply that asks something is the whole turn: Jarvis
    # cannot continue without an answer, and waiting silently means waiting for
    # one nobody knows is wanted.
    if "?" in reply:
        return ReplyVoice.SPEAK
    return ReplyVoice.SPEAK
