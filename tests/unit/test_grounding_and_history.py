"""Source labelling, tool-grounded success, history and personality.

PRD FR-045, FR-046, FR-047, FR-048, FR-043, FR-044, AT-014, AT-018.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from jarvis.core.tools.contract import ToolOutcome, Verification
from jarvis.llm.grounding import SourceLabel, claims_completion, review_response
from jarvis.llm.history import ConversationStore
from jarvis.llm.personality import (
    Formality,
    Humour,
    PersonalityStore,
    ProposalStatus,
    Verbosity,
)
from jarvis.llm.ports import ChatRole
from jarvis.llm.routing import ModelBusyError, ModelRouter
from jarvis.llm.ports import ModelRole


@dataclass
class FakeResult:
    """Stands in for a ToolResult with the two fields grounding reads."""

    succeeded: bool
    verification: Verification
    outcome: ToolOutcome = ToolOutcome.SUCCEEDED


VERIFIED = FakeResult(True, Verification.VERIFIED)
UNVERIFIED = FakeResult(True, Verification.UNVERIFIED)
READ_ONLY = FakeResult(True, Verification.NOT_APPLICABLE)
FAILED = FakeResult(False, Verification.FAILED, ToolOutcome.FAILED)


# -- FR-047 source labelling ------------------------------------------------
def test_an_answer_with_no_tool_is_labelled_as_the_models_own() -> None:
    review = review_response("Paris is the capital of France.")
    assert review.label is SourceLabel.MODEL_ANSWER


def test_a_verified_tool_result_is_labelled_as_such() -> None:
    review = review_response("Brave is open.", tool_results=(VERIFIED,))
    assert review.label is SourceLabel.TOOL_RESULT


def test_an_unverified_tool_run_is_an_inference_not_a_tool_result() -> None:
    """A state-changing tool that could not confirm has not established a fact."""
    review = review_response("Something happened.", tool_results=(UNVERIFIED,))
    assert review.label is SourceLabel.INFERENCE


def test_a_read_only_tool_result_is_still_a_tool_result() -> None:
    """``not_applicable`` means nothing changed, so there was nothing to verify.

    What the tool returned is a real observation, not a guess — so labelling it
    as an inference would understate it.
    """
    review = review_response("Ollama is reachable.", tool_results=(READ_ONLY,))
    assert review.label is SourceLabel.TOOL_RESULT


def test_a_read_only_result_still_cannot_license_a_success_claim() -> None:
    """It can report state; it cannot confirm that an action happened."""
    review = review_response("I've opened Brave for you.", tool_results=(READ_ONLY,))
    assert review.amended
    assert not review.verified_by_tool


def test_retrieval_is_labelled_separately_from_the_model() -> None:
    review = review_response("The file says 42.", retrieved=True)
    assert review.label is SourceLabel.RETRIEVED_FACT


def test_uncertainty_outranks_every_other_label() -> None:
    review = review_response("Possibly.", tool_results=(VERIFIED,), uncertain=True)
    assert review.label is SourceLabel.UNCERTAINTY


def test_every_label_has_wording_for_the_user() -> None:
    for label in SourceLabel:
        assert label.display


# -- FR-048 / AT-018 tool-grounded success ---------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "I've opened Brave for you.",
        "I have launched Sea of Thieves.",
        "Sea of Thieves is now running.",
        "The file has been deleted.",
        "Done.",
        "Successfully created the folder.",
    ],
)
def test_completion_claims_are_recognised(text: str) -> None:
    assert claims_completion(text)


@pytest.mark.parametrize(
    "text",
    [
        "Would you like me to open Brave?",
        "Brave is a web browser.",
        "I can open that if you want.",
        "",
        # Observed against the real model: refusing a destructive request
        # used to trip the completion detector on the bare word "done", so a
        # correct refusal was prefixed with a confusing disclaimer.
        "Deleting every file is the wrong thing to have done.",
        "That is not something I would have done without asking.",
    ],
)
def test_ordinary_sentences_are_not_completion_claims(text: str) -> None:
    assert not claims_completion(text)


@pytest.mark.parametrize("text", ["Done.", "Done", "All set.", "Opened it.\nDone."])
def test_done_as_a_whole_statement_is_still_a_completion_claim(text: str) -> None:
    assert claims_completion(text)


def test_an_unverified_success_claim_is_rewritten() -> None:
    """AT-018: never report completed when it could not be verified."""
    review = review_response("I've opened Brave for you.", tool_results=(UNVERIFIED,))
    assert review.amended
    assert not review.honest
    assert "could not confirm" in review.text
    assert "I've opened Brave for you." in review.text


def test_a_success_claim_with_no_tool_at_all_says_nothing_happened() -> None:
    review = review_response("I have deleted that file.")
    assert review.amended
    assert "no tool ran" in review.text


def test_a_verified_success_claim_is_left_alone() -> None:
    review = review_response("I've opened Brave for you.", tool_results=(VERIFIED,))
    assert not review.amended
    assert review.honest
    assert review.text == "I've opened Brave for you."


def test_a_failed_tool_does_not_verify_anything() -> None:
    review = review_response("Done.", tool_results=(FAILED,))
    assert review.amended
    assert not review.verified_by_tool


# -- FR-045 / FR-046 / AT-014 history and private sessions -----------------
def test_a_normal_conversation_is_recorded(database, audit) -> None:
    store = ConversationStore(database, audit)
    conversation = store.start("Recorded")
    store.add(conversation.conversation_id, ChatRole.USER, "hello")
    store.add(conversation.conversation_id, ChatRole.ASSISTANT, "hi")
    store.end(conversation.conversation_id)

    assert store.count() == 1
    assert len(store.turns(conversation.conversation_id)) == 2


def test_a_private_session_writes_nothing_at_all(database, audit) -> None:
    """AT-014, structurally: not written, rather than written then removed."""
    store = ConversationStore(database, audit)
    conversation = store.start("Private", persist=False)
    store.add(conversation.conversation_id, ChatRole.USER, "a private thing")
    store.add(conversation.conversation_id, ChatRole.ASSISTANT, "understood")

    assert conversation.private
    assert store.count() == 0
    assert database.query_all("SELECT * FROM message") == []

    store.end(conversation.conversation_id)
    assert store.turns(conversation.conversation_id) == ()
    assert database.query_all("SELECT * FROM conversation") == []


def test_a_private_conversation_still_works_in_memory(database, audit) -> None:
    store = ConversationStore(database, audit)
    conversation = store.start("Private", persist=False)
    store.add(conversation.conversation_id, ChatRole.USER, "remember this for now")
    assert len(store.turns(conversation.conversation_id)) == 1


def test_disabling_history_globally_affects_new_conversations(database, audit) -> None:
    store = ConversationStore(database, audit)
    store.set_history_enabled(False)
    conversation = store.start("Not recorded")
    store.add(conversation.conversation_id, ChatRole.USER, "hello")
    assert store.count() == 0
    assert conversation.private


def test_going_private_mid_conversation_erases_what_was_written(database, audit) -> None:
    """Leaving half a transcript satisfies neither reading of the request."""
    store = ConversationStore(database, audit)
    conversation = store.start("Started public")
    store.add(conversation.conversation_id, ChatRole.USER, "something regrettable")
    assert store.count() == 1

    assert store.go_private(conversation.conversation_id) is True
    assert store.count() == 0
    assert database.query_all("SELECT * FROM message") == []

    store.add(conversation.conversation_id, ChatRole.USER, "and more")
    assert store.count() == 0


def test_going_private_twice_is_harmless(database, audit) -> None:
    store = ConversationStore(database, audit)
    conversation = store.start("t")
    assert store.go_private(conversation.conversation_id) is True
    assert store.go_private(conversation.conversation_id) is False


def test_deleting_a_conversation_removes_its_messages(database, audit) -> None:
    store = ConversationStore(database, audit)
    conversation = store.start("t")
    store.add(conversation.conversation_id, ChatRole.USER, "hello")
    store.end(conversation.conversation_id)

    assert store.delete(conversation.conversation_id) is True
    assert database.query_all("SELECT * FROM message") == []


def test_all_history_can_be_deleted(database, audit) -> None:
    store = ConversationStore(database, audit)
    for index in range(3):
        conversation = store.start(f"t{index}")
        store.end(conversation.conversation_id)
    assert store.delete_all() == 3
    assert store.count() == 0


def test_adding_to_an_unknown_conversation_is_an_error(database, audit) -> None:
    store = ConversationStore(database, audit)
    with pytest.raises(KeyError):
        store.add("no-such-conversation", ChatRole.USER, "hello")


# -- FR-041 model routing ---------------------------------------------------
def test_each_role_resolves_to_its_configured_profile(config) -> None:
    router = ModelRouter(config)
    assert router.resolve(ModelRole.CONVERSATION).name == config.models.planner.name
    assert router.resolve(ModelRole.VISION).name == config.models.vision.name
    assert router.resolve(ModelRole.EMBEDDING).name == config.models.embeddings.name


def test_nothing_is_hard_coded_in_the_router(config) -> None:
    router = ModelRouter(config)
    for routed in router.describe_all():
        assert routed.name
        assert routed.context_length > 0


def test_sequential_loading_refuses_a_second_heavy_model(config) -> None:
    """PRD FR-039: 12 GB will not hold two heavy models with large contexts."""
    router = ModelRouter(config)
    assert router.sequential

    with router.hold(ModelRole.CONVERSATION):
        with pytest.raises(ModelBusyError, match="sequential"):
            with router.hold(ModelRole.VISION):
                pass


def test_embeddings_are_light_enough_to_run_alongside(config) -> None:
    router = ModelRouter(config)
    with router.hold(ModelRole.CONVERSATION):
        with router.hold(ModelRole.EMBEDDING) as routed:
            assert routed.name == config.models.embeddings.name


def test_the_hold_is_released_even_when_the_body_raises(config) -> None:
    router = ModelRouter(config)
    with pytest.raises(RuntimeError):
        with router.hold(ModelRole.CONVERSATION):
            raise RuntimeError("boom")
    assert router.held_role is None


# -- FR-043 / FR-044 personality -------------------------------------------
def test_a_default_profile_is_created_once(database, audit) -> None:
    store = PersonalityStore(database, audit)
    first = store.ensure_default()
    second = store.ensure_default()
    assert first.profile_id == second.profile_id
    assert first.active


def test_the_profile_becomes_style_instructions_only(database, audit) -> None:
    store = PersonalityStore(database, audit)
    store.ensure_default()
    prompt = store.system_prompt()
    assert prompt
    # Style, never authority: the profile must not grant anything.
    for word in ("permission", "allow", "authorise", "approve"):
        assert word not in prompt.lower()


def test_the_user_can_edit_the_profile(database, audit) -> None:
    store = PersonalityStore(database, audit)
    profile = store.ensure_default()
    updated = store.update(
        profile.profile_id, formality=Formality.FORMAL.value, address_as="Sir"
    )
    assert updated.formality is Formality.FORMAL
    assert "Sir" in store.system_prompt()


def test_an_impossible_personality_value_is_refused(database, audit) -> None:
    store = PersonalityStore(database, audit)
    profile = store.ensure_default()
    with pytest.raises(ValueError):
        store.update(profile.profile_id, humour="sarcastic-beyond-repair")
    with pytest.raises(ValueError):
        store.update(profile.profile_id, favourite_colour="blue")


def test_a_proposal_changes_nothing_until_the_user_accepts(database, audit) -> None:
    """PRD section 4.4: no silent learning."""
    store = PersonalityStore(database, audit)
    profile = store.ensure_default()
    before = store.active()

    proposal = store.propose(
        profile.profile_id, "humour", Humour.PLAYFUL.value, evidence="user laughed twice"
    )
    assert proposal.status is ProposalStatus.PENDING
    assert store.active() == before, "a proposal must not change behaviour"
    assert len(store.pending_proposals()) == 1


def test_accepting_a_proposal_applies_it(database, audit) -> None:
    store = PersonalityStore(database, audit)
    profile = store.ensure_default()
    proposal = store.propose(profile.profile_id, "verbosity", Verbosity.BRIEF.value)

    updated = store.decide(proposal.proposal_id, accept=True)
    assert updated is not None
    assert updated.verbosity is Verbosity.BRIEF
    assert store.pending_proposals() == ()


def test_rejecting_a_proposal_leaves_the_profile_alone(database, audit) -> None:
    store = PersonalityStore(database, audit)
    profile = store.ensure_default()
    before = store.active()
    proposal = store.propose(profile.profile_id, "verbosity", Verbosity.DETAILED.value)

    store.decide(proposal.proposal_id, accept=False)
    assert store.active() == before
    assert store.pending_proposals() == ()


def test_a_proposal_cannot_be_decided_twice(database, audit) -> None:
    store = PersonalityStore(database, audit)
    profile = store.ensure_default()
    proposal = store.propose(profile.profile_id, "verbosity", Verbosity.BRIEF.value)

    assert store.decide(proposal.proposal_id, accept=True) is not None
    assert store.decide(proposal.proposal_id, accept=True) is None


def test_a_proposal_for_an_unknown_field_is_refused(database, audit) -> None:
    store = PersonalityStore(database, audit)
    profile = store.ensure_default()
    with pytest.raises(ValueError):
        store.propose(profile.profile_id, "authority", "unlimited")
