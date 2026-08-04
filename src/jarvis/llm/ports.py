"""The chat provider boundary (ARCHITECTURE.md section 8, PRD FR-040, section 13.4).

The single most important thing in this module is the shape of
:class:`ChatResponse`: **free text and tool calls are separate fields**.

A response's ``text`` is something to show or speak. Its ``tool_calls`` are
structured proposals with a tool id and typed parameters. Nothing ever parses
``text`` looking for an action, because the moment prose can become an effect,
every document, web page and transcript the model has seen becomes a command
channel (SECURITY.md section 2, PRD section 11.4).

A proposal is still only a proposal. It goes to ``ToolInvoker`` and through all
six checks — allow-list, schema, permission, locks, approval, execute — exactly
like a tool call from any other origin.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, Sequence, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

# L2 -> L3 is the permitted direction: jarvis.llm may depend on jarvis.core.
from jarvis.core.observations import Observation

__all__ = [
    "ChatRole",
    "ChatMessage",
    "ToolCallProposal",
    "ChatResponse",
    "ChatProvider",
    "ChatProviderError",
    "ModelRole",
]


class ChatProviderError(RuntimeError):
    """The provider could not answer. Never a partial or invented answer."""


class ModelRole(str, Enum):
    """Which configured model profile a request should use (PRD FR-041)."""

    CONVERSATION = "conversation"
    VISION = "vision"
    EMBEDDING = "embedding"


class ChatRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """One turn. ``untrusted`` marks content that came from outside.

    Anything observed rather than said by the user — a web page, a document, a
    tool result quoting external content — is carried with ``untrusted=True`` so
    the prompt builder can wrap it as an observation rather than an instruction
    (PRD section 11.4, SECURITY.md section 2).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: ChatRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    untrusted: bool = False
    source_label: str | None = None

    @classmethod
    def from_observation(cls, observation: "Observation") -> "ChatMessage":
        """The only route from observed content into a prompt.

        ``untrusted`` is set here, unconditionally, and is not a parameter of
        this constructor. The flag on its own was a discipline every call site
        had to remember, and a control that holds until one call site forgets is
        not a control — so anything arriving as an `Observation` is wrapped as
        data whether or not the caller thought about it (PRD §11.4).

        This lives in L3 rather than on `Observation` itself because
        `jarvis.core` is L2 and must not know about `jarvis.llm`. Dependencies
        point downward, and `tests/security/test_layering.py` enforces that even
        for an import tucked inside a function body.
        """
        return cls(
            role=ChatRole.TOOL,
            content=observation.text,
            untrusted=True,
            source_label=observation.source_label,
        )


class ToolCallProposal(BaseModel):
    """A structured action the model is asking for. Not permission to take it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tool_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    call_id: str | None = None


class ChatResponse(BaseModel):
    """What a provider returned.

    ``text`` is for the user. ``tool_calls`` is for the invoker. Nothing
    promotes one into the other.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str = ""
    tool_calls: tuple[ToolCallProposal, ...] = ()
    model: str = ""
    finish_reason: str | None = None
    truncated: bool = False
    prompt_tokens: int | None = None
    completion_tokens: int | None = None

    @property
    def proposes_action(self) -> bool:
        return bool(self.tool_calls)


@runtime_checkable
class ChatProvider(Protocol):
    """Completes a conversation. Implementations are adapters over a runtime."""

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        tools: Sequence[dict[str, Any]] = (),
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> ChatResponse:
        ...

    @property
    def available(self) -> bool:
        ...
