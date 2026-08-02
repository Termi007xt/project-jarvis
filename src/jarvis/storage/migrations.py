"""Versioned forward-only schema migrations (ADR-0002, PRD NFR-043).

Rules:

* Migrations are append-only. Never edit a released migration; add a new one.
* ``PRAGMA user_version`` holds the applied version; ``schema_migration``
  records what was applied and when.
* A database newer than this build is a hard startup failure. Reading it
  best-effort would risk writing records the newer schema cannot interpret.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from jarvis.common import to_iso, utc_now
from jarvis.storage.database import Database, DatabaseError

__all__ = [
    "MIGRATIONS",
    "Migration",
    "SCHEMA_VERSION",
    "migrate",
    "applied_migrations",
    "split_statements",
]


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str


_M001_FOUNDATION = """
CREATE TABLE schema_migration (
    version     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    applied_at  TEXT NOT NULL
);

-- One row per application launch. Used to detect locks and tasks orphaned by a
-- crash (PRD FR-006, NFR-010).
CREATE TABLE runtime_instance (
    instance_id TEXT PRIMARY KEY,
    pid         INTEGER NOT NULL,
    app_version TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    stopped_at  TEXT
);

-- Append-only audit index. The tamper-evident record is logs/audit.jsonl;
-- this table exists so the GUI can search it (PRD section 11.5).
CREATE TABLE audit_event (
    audit_id            TEXT PRIMARY KEY,
    occurred_at         TEXT NOT NULL,
    instance_id         TEXT,
    category            TEXT NOT NULL,
    actor               TEXT NOT NULL,
    task_id             TEXT,
    conversation_id     TEXT,
    tool_id             TEXT,
    capability_id       TEXT,
    risk                TEXT,
    permission_decision TEXT,
    summary             TEXT NOT NULL,
    parameters_json     TEXT,
    pre_state_json      TEXT,
    result              TEXT,
    verification        TEXT,
    error               TEXT,
    evidence_ref        TEXT
);
CREATE INDEX ix_audit_event_occurred_at ON audit_event (occurred_at);
CREATE INDEX ix_audit_event_task        ON audit_event (task_id);
CREATE INDEX ix_audit_event_category    ON audit_event (category);
CREATE INDEX ix_audit_event_capability  ON audit_event (capability_id);

-- Permission grants (PRD section 9.9). A grant is never implicit: absence of a
-- row means "ask" or "deny", never "allow".
CREATE TABLE permission_grant (
    grant_id      TEXT PRIMARY KEY,
    capability_id TEXT NOT NULL,
    decision      TEXT NOT NULL,
    scope         TEXT NOT NULL,
    scope_ref     TEXT,
    session_id    TEXT,
    task_id       TEXT,
    created_at    TEXT NOT NULL,
    created_by    TEXT NOT NULL,
    expires_at    TEXT,
    revoked_at    TEXT,
    reason        TEXT
);
CREATE INDEX ix_permission_grant_capability ON permission_grant (capability_id);
CREATE INDEX ix_permission_grant_session    ON permission_grant (session_id);
CREATE INDEX ix_permission_grant_task       ON permission_grant (task_id);

-- Persistent task state machine (PRD FR-120 .. FR-133).
CREATE TABLE task (
    task_id             TEXT PRIMARY KEY,
    parent_task_id      TEXT REFERENCES task (task_id) ON DELETE CASCADE,
    conversation_id     TEXT,
    name                TEXT NOT NULL,
    goal                TEXT NOT NULL,
    runner_id           TEXT NOT NULL,
    state               TEXT NOT NULL,
    priority            INTEGER NOT NULL DEFAULT 100,
    required_locks_json TEXT NOT NULL DEFAULT '[]',
    payload_json        TEXT NOT NULL DEFAULT '{}',
    attempts            INTEGER NOT NULL DEFAULT 0,
    max_retries         INTEGER NOT NULL DEFAULT 3,
    waiting_on          TEXT,
    blocked_reason      TEXT,
    failure_code        TEXT,
    result_summary      TEXT,
    recovered           INTEGER NOT NULL DEFAULT 0,
    instance_id         TEXT,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    started_at          TEXT,
    ended_at            TEXT
);
CREATE INDEX ix_task_state    ON task (state);
CREATE INDEX ix_task_parent   ON task (parent_task_id);
CREATE INDEX ix_task_instance ON task (instance_id);

CREATE TABLE task_transition (
    transition_id TEXT PRIMARY KEY,
    task_id       TEXT NOT NULL REFERENCES task (task_id) ON DELETE CASCADE,
    from_state    TEXT,
    to_state      TEXT NOT NULL,
    reason        TEXT,
    occurred_at   TEXT NOT NULL
);
CREATE INDEX ix_task_transition_task ON task_transition (task_id, occurred_at);

CREATE TABLE task_checkpoint (
    checkpoint_id TEXT PRIMARY KEY,
    task_id       TEXT NOT NULL REFERENCES task (task_id) ON DELETE CASCADE,
    sequence      INTEGER NOT NULL,
    label         TEXT NOT NULL,
    state_json    TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    UNIQUE (task_id, sequence)
);

-- Evidence supporting a completion claim (PRD FR-132, FR-048).
CREATE TABLE task_evidence (
    evidence_id   TEXT PRIMARY KEY,
    task_id       TEXT NOT NULL REFERENCES task (task_id) ON DELETE CASCADE,
    kind          TEXT NOT NULL,
    summary       TEXT NOT NULL,
    detail_json   TEXT,
    artefact_path TEXT,
    created_at    TEXT NOT NULL
);
CREATE INDEX ix_task_evidence_task ON task_evidence (task_id);

-- Exclusive resource locks (PRD FR-124). The primary key IS the mutual
-- exclusion: one row per lock name, or no row.
CREATE TABLE resource_lock (
    lock_name   TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL,
    instance_id TEXT NOT NULL,
    acquired_at TEXT NOT NULL
);

-- One row per tool execution attempt, for the metrics in PRD section 24.
CREATE TABLE tool_invocation (
    invocation_id TEXT PRIMARY KEY,
    tool_id       TEXT NOT NULL,
    tool_version  TEXT NOT NULL,
    task_id       TEXT,
    outcome       TEXT NOT NULL,
    failure_code  TEXT,
    verification  TEXT NOT NULL,
    attempts      INTEGER NOT NULL,
    started_at    TEXT NOT NULL,
    ended_at      TEXT NOT NULL,
    duration_ms   INTEGER NOT NULL
);
CREATE INDEX ix_tool_invocation_tool ON tool_invocation (tool_id, started_at);
CREATE INDEX ix_tool_invocation_task ON tool_invocation (task_id);
"""


_M002_SECRETS_AND_CONVERSATION = """
-- Protected secrets (ADR-0030, PRD 18.3, NFR-022). The value is DPAPI
-- ciphertext and is never queryable; the metadata beside it is not sensitive
-- and is what the Integrations screen lists so a user can see, and delete,
-- what is stored. Excluded from normal exports (FR-169, AT-016).
CREATE TABLE secret (
    name          TEXT PRIMARY KEY,
    purpose       TEXT NOT NULL,
    owner         TEXT NOT NULL,
    ciphertext    BLOB NOT NULL,
    protection    TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    last_used_at  TEXT
);

-- Conversation history (PRD FR-045). A private session (FR-046, AT-014)
-- never writes a row here at all; ``persisted`` records the choice for
-- conversations that did, so history controls can explain themselves.
CREATE TABLE conversation (
    conversation_id TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    started_at      TEXT NOT NULL,
    ended_at        TEXT,
    model           TEXT,
    persisted       INTEGER NOT NULL DEFAULT 1,
    message_count   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX ix_conversation_started ON conversation (started_at);

-- One turn. ``source_label`` is the FR-047 grounding label: whether this came
-- from the model, a retrieved fact, an inference, a tool result, or is an
-- admission of uncertainty.
CREATE TABLE message (
    message_id      TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversation (conversation_id) ON DELETE CASCADE,
    sequence        INTEGER NOT NULL,
    role            TEXT NOT NULL,
    content         TEXT NOT NULL,
    source_label    TEXT,
    tool_id         TEXT,
    task_id         TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX ix_message_conversation ON message (conversation_id, sequence);

-- The personality profile (PRD FR-043). Editable by the user; never learned
-- silently (PRD 4.4, FR-044 proposals are approval-gated).
CREATE TABLE personality_profile (
    profile_id  TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    formality   TEXT NOT NULL,
    humour      TEXT NOT NULL,
    verbosity   TEXT NOT NULL,
    address_as  TEXT,
    active      INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- A proposed personality or humour adjustment awaiting the user's decision.
-- Nothing here affects behaviour until it is approved (PRD 4.4, FR-044).
CREATE TABLE personality_proposal (
    proposal_id TEXT PRIMARY KEY,
    profile_id  TEXT NOT NULL REFERENCES personality_profile (profile_id) ON DELETE CASCADE,
    field       TEXT NOT NULL,
    current_value TEXT,
    proposed_value TEXT NOT NULL,
    evidence    TEXT,
    status      TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    decided_at  TEXT
);
CREATE INDEX ix_personality_proposal_status ON personality_proposal (status);
"""


_M003_WAKE_ENROLMENT = """
-- Wake-word enrolment (ADR-0016). One row per enrolment attempt, keeping the
-- measurement that decided whether always-listening could be enabled. Criterion
-- 1 is explicit that "we trained a model" without a measurement does not count,
-- so the measurement is stored, not just the verdict.
--
-- Recordings are personal data (criterion 3): they live under the vault as
-- files, are listed in the Voice screen, are deletable, and are excluded from
-- normal exports. Only their paths are recorded here.
CREATE TABLE wake_enrolment (
    enrolment_id     TEXT PRIMARY KEY,
    phrase           TEXT NOT NULL,
    threshold        REAL NOT NULL,
    sample_count     INTEGER NOT NULL,
    true_accept_rate REAL NOT NULL,
    false_accept_rate REAL NOT NULL,
    passed           INTEGER NOT NULL,
    active           INTEGER NOT NULL DEFAULT 0,
    measured_summary TEXT NOT NULL,
    created_at       TEXT NOT NULL
);
CREATE INDEX ix_wake_enrolment_active ON wake_enrolment (active);

CREATE TABLE wake_enrolment_sample (
    sample_id    TEXT PRIMARY KEY,
    enrolment_id TEXT NOT NULL REFERENCES wake_enrolment (enrolment_id) ON DELETE CASCADE,
    path         TEXT NOT NULL,
    score        REAL,
    held_out     INTEGER NOT NULL DEFAULT 0,
    recorded_at  TEXT NOT NULL
);
CREATE INDEX ix_wake_enrolment_sample_enrolment ON wake_enrolment_sample (enrolment_id);
"""


MIGRATIONS: tuple[Migration, ...] = (
    Migration(version=1, name="phase0_foundation", sql=_M001_FOUNDATION),
    Migration(version=2, name="phase1_secrets_and_conversation",
              sql=_M002_SECRETS_AND_CONVERSATION),
    Migration(version=3, name="phase1_wake_enrolment", sql=_M003_WAKE_ENROLMENT),
)

SCHEMA_VERSION = MIGRATIONS[-1].version


def applied_migrations(database: Database) -> list[tuple[int, str, str]]:
    row = database.query_one(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'schema_migration'"
    )
    if row is None:
        return []
    return [
        (int(r["version"]), str(r["name"]), str(r["applied_at"]))
        for r in database.query_all(
            "SELECT version, name, applied_at FROM schema_migration ORDER BY version"
        )
    ]


def split_statements(sql: str) -> list[str]:
    """Split a migration script into individual statements.

    ``sqlite3.Connection.executescript`` implicitly commits any open
    transaction, which would defeat the all-or-nothing wrapper around a
    migration. Statements are therefore executed one at a time inside our own
    transaction.

    Comments are removed **before** splitting. Removing them afterwards means a
    semicolon inside a comment splits the script mid-sentence, and the prose
    after it is handed to SQLite as though it were SQL — which fails with a
    syntax error pointing at an English word rather than at the comment.

    Compound ``BEGIN ... END`` blocks (triggers) are rejected rather than
    mis-split: a migration that needs one must add explicit handling first.
    """
    if re.search(r"\bBEGIN\b", sql, re.IGNORECASE):
        raise DatabaseError(
            "migration contains a compound BEGIN...END block, which the simple "
            "statement splitter cannot handle safely"
        )
    without_comments = "\n".join(
        line for line in sql.splitlines() if not line.strip().startswith("--")
    )
    return [chunk.strip() for chunk in without_comments.split(";") if chunk.strip()]


def migrate(database: Database) -> int:
    """Apply pending migrations. Returns the resulting schema version."""
    current = database.user_version()

    if current > SCHEMA_VERSION:
        raise DatabaseError(
            f"database schema version {current} is newer than this build supports "
            f"({SCHEMA_VERSION}). Refusing to open it: writing with an older schema "
            f"could corrupt records the newer version depends on. Upgrade the "
            f"application or restore an older backup of the vault."
        )

    for migration in MIGRATIONS:
        if migration.version <= current:
            continue
        with database.transaction() as connection:
            for statement in split_statements(migration.sql):
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migration (version, name, applied_at) VALUES (?, ?, ?)",
                (migration.version, migration.name, to_iso(utc_now())),
            )
            connection.execute(f"PRAGMA user_version = {int(migration.version)}")
        current = migration.version

    return current
