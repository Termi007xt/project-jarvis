"""AT-014 — a private session produces no permanent record after it ends.

Asserted against the real vault on disk, not against the store's own reporting:
the database file and the audit log are read back as bytes and searched for what
was said. A cleanup step that ran but missed something would still pass a test
that only asked the store whether it thought it was empty.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.llm.ports import ChatRole
from jarvis.runtime.core import JarvisCore

PRIVATE_PHRASE = "my resignation letter is in the blue folder"
NORMAL_PHRASE = "what is the weather like"


def _vault_bytes(core: JarvisCore) -> bytes:
    """Everything the vault has written, as raw bytes."""
    core.database.checkpoint()
    blob = b""
    for path in Path(core.paths.root).rglob("*"):
        if path.is_file():
            try:
                blob += path.read_bytes()
            except OSError:  # pragma: no cover - a locked file is still a file
                continue
    return blob


def test_a_private_session_leaves_no_record_anywhere(core: JarvisCore) -> None:
    conversation = core.start_conversation("Private", private=True)
    core.history.add(conversation.conversation_id, ChatRole.USER, PRIVATE_PHRASE)
    core.history.add(conversation.conversation_id, ChatRole.ASSISTANT, "understood")
    core.history.end(conversation.conversation_id)

    assert core.history.count() == 0
    assert PRIVATE_PHRASE.encode("utf-8") not in _vault_bytes(core)


def test_a_normal_session_is_recorded_so_the_test_above_means_something(
    core: JarvisCore,
) -> None:
    """A control: prove the byte search would have found it if written."""
    conversation = core.start_conversation("Normal")
    core.history.add(conversation.conversation_id, ChatRole.USER, NORMAL_PHRASE)
    core.history.end(conversation.conversation_id)

    assert core.history.count() == 1
    assert NORMAL_PHRASE.encode("utf-8") in _vault_bytes(core)


def test_a_private_conversation_is_marked_private_to_the_user(core: JarvisCore) -> None:
    conversation = core.start_conversation("Private", private=True)
    assert conversation.private
    assert not conversation.persisted


def test_ending_a_private_session_discards_its_in_memory_turns(core: JarvisCore) -> None:
    conversation = core.start_conversation("Private", private=True)
    core.history.add(conversation.conversation_id, ChatRole.USER, PRIVATE_PHRASE)
    assert len(core.history.turns(conversation.conversation_id)) == 1

    core.history.end(conversation.conversation_id)
    assert core.history.turns(conversation.conversation_id) == ()


def test_the_audit_log_records_that_a_private_session_happened_not_what_was_said(
    core: JarvisCore,
) -> None:
    """Privacy is not the same as invisibility: the event is auditable."""
    conversation = core.start_conversation("Private", private=True)
    core.history.add(conversation.conversation_id, ChatRole.USER, PRIVATE_PHRASE)
    core.history.end(conversation.conversation_id)

    audit_text = Path(core.paths.audit_log_path).read_text(encoding="utf-8")
    assert "private conversation started" in audit_text
    assert PRIVATE_PHRASE not in audit_text


def test_history_deleted_by_the_user_stays_deleted(core: JarvisCore) -> None:
    conversation = core.start_conversation("Normal")
    core.history.add(conversation.conversation_id, ChatRole.USER, NORMAL_PHRASE)
    core.history.end(conversation.conversation_id)

    assert core.history.delete_all() == 1
    assert core.history.count() == 0
    assert NORMAL_PHRASE.encode("utf-8") not in _vault_bytes(core)


@pytest.mark.parametrize("private", [True, False])
def test_starting_a_conversation_records_which_model_will_answer(
    core: JarvisCore, private: bool
) -> None:
    conversation = core.start_conversation("t", private=private)
    assert conversation.model == core.config.models.planner.name
