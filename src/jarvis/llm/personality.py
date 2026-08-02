"""Personality profile and humour proposals (PRD FR-043, FR-044, section 4.4).

FR-043 makes the profile user-editable. FR-044 allows Jarvis to *notice* that a
different style might suit better — and section 4.4 forbids it acting on that
noticing. So the proposal flow here is deliberately asymmetric: Jarvis may write
a proposal at any time, and only the user may turn one into a change.

Nothing in this module alters behaviour on its own. ``system_prompt`` reads the
active profile; ``propose`` writes a row that does nothing until approved.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from jarvis.common import from_iso, new_id, to_iso, utc_now
from jarvis.core.audit.log import AuditLog
from jarvis.core.audit.models import AuditCategory
from jarvis.storage.database import Database

__all__ = [
    "PersonalityProfile",
    "PersonalityProposal",
    "PersonalityStore",
    "ProposalStatus",
    "Formality",
    "Humour",
    "Verbosity",
    "DEFAULT_PROFILE_NAME",
]

DEFAULT_PROFILE_NAME = "Default"


class Formality(str, Enum):
    CASUAL = "casual"
    NEUTRAL = "neutral"
    FORMAL = "formal"


class Humour(str, Enum):
    NONE = "none"
    DRY = "dry"
    PLAYFUL = "playful"


class Verbosity(str, Enum):
    BRIEF = "brief"
    BALANCED = "balanced"
    DETAILED = "detailed"


class ProposalStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class PersonalityProfile:
    profile_id: str
    name: str
    formality: Formality
    humour: Humour
    verbosity: Verbosity
    address_as: str | None
    active: bool
    created_at: datetime
    updated_at: datetime

    def describe(self) -> str:
        address = f", addressing you as '{self.address_as}'" if self.address_as else ""
        return (
            f"{self.name}: {self.formality.value}, {self.humour.value} humour, "
            f"{self.verbosity.value}{address}"
        )


@dataclass(frozen=True)
class PersonalityProposal:
    proposal_id: str
    profile_id: str
    field: str
    current_value: str | None
    proposed_value: str
    evidence: str | None
    status: ProposalStatus
    created_at: datetime
    decided_at: datetime | None = None


class PersonalityStore:
    """The active profile, and proposals awaiting the user's decision."""

    _FIELDS = {"formality": Formality, "humour": Humour, "verbosity": Verbosity}

    def __init__(self, database: Database, audit: AuditLog | None = None) -> None:
        self._database = database
        self._audit = audit
        self._lock = threading.RLock()

    # -- profiles ----------------------------------------------------------
    def ensure_default(self) -> PersonalityProfile:
        existing = self.active()
        if existing is not None:
            return existing
        now = utc_now()
        profile = PersonalityProfile(
            profile_id=new_id(),
            name=DEFAULT_PROFILE_NAME,
            formality=Formality.NEUTRAL,
            humour=Humour.DRY,
            verbosity=Verbosity.BALANCED,
            address_as=None,
            active=True,
            created_at=now,
            updated_at=now,
        )
        with self._database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO personality_profile (
                    profile_id, name, formality, humour, verbosity, address_as,
                    active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    profile.profile_id,
                    profile.name,
                    profile.formality.value,
                    profile.humour.value,
                    profile.verbosity.value,
                    profile.address_as,
                    to_iso(now),
                    to_iso(now),
                ),
            )
        return profile

    def active(self) -> PersonalityProfile | None:
        row = self._database.query_one(
            "SELECT * FROM personality_profile WHERE active = 1 LIMIT 1"
        )
        return self._to_profile(row) if row is not None else None

    def update(self, profile_id: str, **changes: object) -> PersonalityProfile:
        """Change the profile. Only the user reaches this (PRD section 4.4)."""
        allowed = {"name", "formality", "humour", "verbosity", "address_as"}
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"not personality fields: {sorted(unknown)}")

        for field_name, enum_type in self._FIELDS.items():
            if field_name in changes and changes[field_name] is not None:
                # Raises for a value outside the enum, rather than storing it.
                changes[field_name] = enum_type(str(changes[field_name])).value

        assignments = ", ".join(f"{key} = ?" for key in changes)
        with self._lock, self._database.transaction() as connection:
            connection.execute(
                f"UPDATE personality_profile SET {assignments}, updated_at = ? "
                "WHERE profile_id = ?",
                (*changes.values(), to_iso(utc_now()), profile_id),
            )
        self._record(f"personality profile updated: {sorted(changes)}")
        updated = self.active()
        assert updated is not None
        return updated

    # -- proposals (FR-044) ------------------------------------------------
    def propose(
        self, profile_id: str, field: str, proposed_value: str, evidence: str | None = None
    ) -> PersonalityProposal:
        """Record a suggested adjustment. Changes nothing by itself."""
        if field not in self._FIELDS:
            raise ValueError(f"'{field}' is not an adjustable personality field")
        self._FIELDS[field](proposed_value)  # reject an impossible value now

        current = self.active()
        proposal = PersonalityProposal(
            proposal_id=new_id(),
            profile_id=profile_id,
            field=field,
            current_value=getattr(current, field).value if current else None,
            proposed_value=proposed_value,
            evidence=evidence,
            status=ProposalStatus.PENDING,
            created_at=utc_now(),
        )
        with self._database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO personality_proposal (
                    proposal_id, profile_id, field, current_value, proposed_value,
                    evidence, status, created_at, decided_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    proposal.proposal_id,
                    profile_id,
                    field,
                    proposal.current_value,
                    proposed_value,
                    evidence,
                    ProposalStatus.PENDING.value,
                    to_iso(proposal.created_at),
                ),
            )
        self._record(f"personality change proposed for '{field}' (not applied)")
        return proposal

    def pending_proposals(self) -> tuple[PersonalityProposal, ...]:
        return tuple(
            self._to_proposal(row)
            for row in self._database.query_all(
                "SELECT * FROM personality_proposal WHERE status = ? ORDER BY created_at",
                (ProposalStatus.PENDING.value,),
            )
        )

    def decide(self, proposal_id: str, accept: bool) -> PersonalityProfile | None:
        """Apply or reject a proposal. This is the only path from proposal to change."""
        row = self._database.query_one(
            "SELECT * FROM personality_proposal WHERE proposal_id = ?", (proposal_id,)
        )
        if row is None or row["status"] != ProposalStatus.PENDING.value:
            return None
        proposal = self._to_proposal(row)

        with self._database.transaction() as connection:
            connection.execute(
                "UPDATE personality_proposal SET status = ?, decided_at = ? "
                "WHERE proposal_id = ?",
                (
                    (ProposalStatus.ACCEPTED if accept else ProposalStatus.REJECTED).value,
                    to_iso(utc_now()),
                    proposal_id,
                ),
            )
        self._record(
            f"personality proposal for '{proposal.field}' "
            f"{'accepted' if accept else 'rejected'} by the user"
        )
        if not accept:
            return self.active()
        return self.update(proposal.profile_id, **{proposal.field: proposal.proposed_value})

    # -- prompt ------------------------------------------------------------
    def system_prompt(self, profile: PersonalityProfile | None = None) -> str:
        """Turn the profile into instructions. Style only, never authority."""
        profile = profile or self.active()
        if profile is None:
            return ""
        tone = {
            Formality.CASUAL: "Speak casually, like a colleague.",
            Formality.NEUTRAL: "Speak plainly and directly.",
            Formality.FORMAL: "Speak formally and precisely.",
        }[profile.formality]
        humour = {
            Humour.NONE: "Do not attempt humour.",
            Humour.DRY: "Dry wit is welcome, but never at the cost of clarity.",
            Humour.PLAYFUL: "A playful tone is welcome when the moment suits it.",
        }[profile.humour]
        length = {
            Verbosity.BRIEF: "Answer in as few words as the question allows.",
            Verbosity.BALANCED: "Answer fully but without padding.",
            Verbosity.DETAILED: "Explain your reasoning as well as your answer.",
        }[profile.verbosity]
        address = f" Address the user as {profile.address_as}." if profile.address_as else ""
        return f"{tone} {humour} {length}{address}"

    # -- internals ---------------------------------------------------------
    @staticmethod
    def _to_profile(row: object) -> PersonalityProfile:
        data = dict(row)  # type: ignore[arg-type]
        return PersonalityProfile(
            profile_id=data["profile_id"],
            name=data["name"],
            formality=Formality(data["formality"]),
            humour=Humour(data["humour"]),
            verbosity=Verbosity(data["verbosity"]),
            address_as=data["address_as"],
            active=bool(data["active"]),
            created_at=from_iso(data["created_at"]),  # type: ignore[arg-type]
            updated_at=from_iso(data["updated_at"]),  # type: ignore[arg-type]
        )

    @staticmethod
    def _to_proposal(row: object) -> PersonalityProposal:
        data = dict(row)  # type: ignore[arg-type]
        return PersonalityProposal(
            proposal_id=data["proposal_id"],
            profile_id=data["profile_id"],
            field=data["field"],
            current_value=data["current_value"],
            proposed_value=data["proposed_value"],
            evidence=data["evidence"],
            status=ProposalStatus(data["status"]),
            created_at=from_iso(data["created_at"]),  # type: ignore[arg-type]
            decided_at=from_iso(data["decided_at"]),
        )

    def _record(self, summary: str) -> None:
        if self._audit is None:
            return
        self._audit.record(AuditCategory.CONFIG, summary, actor="user")
