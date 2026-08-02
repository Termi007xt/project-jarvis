"""Conversation history and private sessions (PRD FR-045, FR-046, AT-014).

A private session is not "history that is hidden afterwards" — it is history
that is **never written**. ``ConversationStore.start`` with ``persist=False``
returns a conversation that holds its turns in memory and writes no row to any
table, so AT-014's "no permanent conversation or memory record after it ends" is
a structural property rather than a cleanup step that could fail or be skipped.

History can also be disabled globally, and turned off for one conversation that
started as a normal one. Turning it off mid-conversation deletes what was
already written for that conversation: the user's intent is "this did not
happen", and leaving a partial transcript would be the worst of both.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime

from jarvis.common import from_iso, new_id, to_iso, utc_now
from jarvis.core.audit.log import AuditLog
from jarvis.core.audit.models import AuditCategory
from jarvis.llm.ports import ChatMessage, ChatRole
from jarvis.storage.database import Database

__all__ = ["Conversation", "ConversationStore", "StoredMessage"]

_LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class StoredMessage:
    message_id: str
    conversation_id: str
    sequence: int
    role: ChatRole
    content: str
    created_at: datetime
    source_label: str | None = None
    tool_id: str | None = None
    task_id: str | None = None

    def to_chat_message(self) -> ChatMessage:
        return ChatMessage(
            role=self.role,
            content=self.content,
            source_label=self.source_label,
        )


@dataclass
class Conversation:
    """One conversation, persisted or not."""

    conversation_id: str
    title: str
    started_at: datetime
    persisted: bool
    model: str | None = None
    ended_at: datetime | None = None
    #: In-memory turns. For a private conversation this is the only copy, and it
    #: is discarded when the conversation ends.
    turns: list[StoredMessage] = field(default_factory=list)

    @property
    def private(self) -> bool:
        return not self.persisted

    @property
    def message_count(self) -> int:
        return len(self.turns)


class ConversationStore:
    """Creates conversations and records turns, when recording is permitted."""

    def __init__(
        self,
        database: Database,
        audit: AuditLog | None = None,
        *,
        history_enabled: bool = True,
    ) -> None:
        self._database = database
        self._audit = audit
        self._history_enabled = history_enabled
        self._lock = threading.RLock()
        self._live: dict[str, Conversation] = {}

    @property
    def history_enabled(self) -> bool:
        return self._history_enabled

    def set_history_enabled(self, enabled: bool) -> None:
        """Global history control (PRD FR-045). Affects new conversations."""
        with self._lock:
            self._history_enabled = enabled
        self._record("history enabled" if enabled else "history disabled", None)

    # -- lifecycle ---------------------------------------------------------
    def start(
        self, title: str = "Conversation", *, persist: bool | None = None, model: str | None = None
    ) -> Conversation:
        """Begin a conversation. ``persist=False`` is a private session."""
        should_persist = self._history_enabled if persist is None else persist
        conversation = Conversation(
            conversation_id=new_id(),
            title=title,
            started_at=utc_now(),
            persisted=should_persist,
            model=model,
        )
        with self._lock:
            self._live[conversation.conversation_id] = conversation

        if should_persist:
            with self._database.transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO conversation (
                        conversation_id, title, started_at, ended_at, model,
                        persisted, message_count
                    ) VALUES (?, ?, ?, NULL, ?, 1, 0)
                    """,
                    (
                        conversation.conversation_id,
                        title,
                        to_iso(conversation.started_at),
                        model,
                    ),
                )
        self._record(
            "private conversation started (nothing will be written)"
            if not should_persist
            else "conversation started",
            conversation.conversation_id,
        )
        return conversation

    def end(self, conversation_id: str) -> None:
        with self._lock:
            conversation = self._live.pop(conversation_id, None)
        if conversation is None:
            return
        conversation.ended_at = utc_now()
        if conversation.persisted:
            with self._database.transaction() as connection:
                connection.execute(
                    "UPDATE conversation SET ended_at = ?, message_count = ? "
                    "WHERE conversation_id = ?",
                    (
                        to_iso(conversation.ended_at),
                        conversation.message_count,
                        conversation_id,
                    ),
                )
        else:
            # The in-memory turns are the only copy and they go with it.
            conversation.turns.clear()
        self._record("conversation ended", conversation_id)

    def go_private(self, conversation_id: str) -> bool:
        """Stop recording this conversation, and erase what was recorded.

        Per-conversation history disable (PRD FR-045). Leaving the earlier half
        of a transcript behind would satisfy neither reading of the request.
        """
        with self._lock:
            conversation = self._live.get(conversation_id)
            if conversation is None or not conversation.persisted:
                return False
            conversation.persisted = False
        self.delete(conversation_id)
        self._record("conversation switched to private; its record was deleted", conversation_id)
        return True

    # -- turns -------------------------------------------------------------
    def add(
        self,
        conversation_id: str,
        role: ChatRole,
        content: str,
        *,
        source_label: str | None = None,
        tool_id: str | None = None,
        task_id: str | None = None,
    ) -> StoredMessage:
        with self._lock:
            conversation = self._live.get(conversation_id)
            if conversation is None:
                raise KeyError(f"no live conversation '{conversation_id}'")
            sequence = len(conversation.turns) + 1
            message = StoredMessage(
                message_id=new_id(),
                conversation_id=conversation_id,
                sequence=sequence,
                role=role,
                content=content,
                created_at=utc_now(),
                source_label=source_label,
                tool_id=tool_id,
                task_id=task_id,
            )
            conversation.turns.append(message)
            persisted = conversation.persisted

        if persisted:
            with self._database.transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO message (
                        message_id, conversation_id, sequence, role, content,
                        source_label, tool_id, task_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        message.message_id,
                        conversation_id,
                        sequence,
                        role.value,
                        content,
                        source_label,
                        tool_id,
                        task_id,
                        to_iso(message.created_at),
                    ),
                )
                connection.execute(
                    "UPDATE conversation SET message_count = ? WHERE conversation_id = ?",
                    (sequence, conversation_id),
                )
        return message

    # -- reading -----------------------------------------------------------
    def live(self, conversation_id: str) -> Conversation | None:
        with self._lock:
            return self._live.get(conversation_id)

    def turns(self, conversation_id: str) -> tuple[StoredMessage, ...]:
        """Turns for a live conversation, from memory; otherwise from storage."""
        with self._lock:
            conversation = self._live.get(conversation_id)
            if conversation is not None:
                return tuple(conversation.turns)
        return tuple(
            StoredMessage(
                message_id=str(row["message_id"]),
                conversation_id=str(row["conversation_id"]),
                sequence=int(row["sequence"]),
                role=ChatRole(row["role"]),
                content=str(row["content"]),
                created_at=from_iso(row["created_at"]),  # type: ignore[arg-type]
                source_label=row["source_label"],
                tool_id=row["tool_id"],
                task_id=row["task_id"],
            )
            for row in self._database.query_all(
                "SELECT * FROM message WHERE conversation_id = ? ORDER BY sequence",
                (conversation_id,),
            )
        )

    def recent(self, limit: int = 50) -> tuple[dict[str, object], ...]:
        return tuple(
            dict(row)
            for row in self._database.query_all(
                "SELECT * FROM conversation ORDER BY started_at DESC LIMIT ?", (limit,)
            )
        )

    def count(self) -> int:
        row = self._database.query_one("SELECT COUNT(*) AS n FROM conversation")
        return int(row["n"]) if row else 0

    # -- deletion ----------------------------------------------------------
    def delete(self, conversation_id: str) -> bool:
        """Remove a conversation and its turns. Messages cascade."""
        with self._database.transaction() as connection:
            cursor = connection.execute(
                "DELETE FROM conversation WHERE conversation_id = ?", (conversation_id,)
            )
            removed = cursor.rowcount > 0
        if removed:
            self._record("conversation deleted", conversation_id)
        return removed

    def delete_all(self) -> int:
        with self._database.transaction() as connection:
            cursor = connection.execute("DELETE FROM conversation")
            removed = cursor.rowcount
        self._record(f"all conversation history deleted ({removed})", None)
        return removed

    # -- internals ---------------------------------------------------------
    def _record(self, summary: str, conversation_id: str | None) -> None:
        if self._audit is None:
            return
        self._audit.record(
            AuditCategory.CONFIG,
            summary,
            actor="user",
            conversation_id=conversation_id,
        )
