# ADR-0002: SQLite as the Single Source of Truth

- **Status:** Accepted
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §14.1, §14.2, §14.3, NFR-025, NFR-043, FR-167
- **Phase:** 0

## Context

Project Jarvis accumulates a large and heterogeneous set of user-owned state
from Phase 0 onwards: configuration overrides, tasks and their state machine,
resource locks, permission grants and decisions, audit events, and — from
Phase 1 onwards — conversations, memories, skills, application mappings and
much more (PRD §14.3 lists over forty entities). This state must survive
crashes (NFR-010), be exportable to human-readable form, be fully deletable
on request (NFR-025), and be safe to query concurrently from a scheduler
thread, worker threads and the GUI thread at once.

At the same time, the vault also has to hold large binary artefacts —
screenshots, audio diagnostics, task evidence — and a derived embedding index
that Phase 3/4 memory retrieval depends on. Mixing "the record of what
happened" with "a rebuildable search structure over what happened" in the
same store, or spreading canonical facts across several independent stores,
is a well-known way to end up with silent disagreement between them.

The requirement that decides this ADR is explicit in the PRD: "The canonical
source of truth shall be a local SQLite database named `jarvis.db` ... Derived
indexes and caches must be rebuildable and must not contain unique
information" (PRD §14.1).

## Options considered

### Option A — SQLite as canonical store, everything else derived
**Pros:** One transactional writer with ACID guarantees; mature, embedded,
zero-install, ships with Python; WAL mode gives concurrent readers alongside
a single writer, which matches the actual access pattern (scheduler writes,
GUI and audit reads); foreign keys give correct cascading deletion of derived
data (FR-167); a single file (plus WAL/SHM siblings) is trivial to back up,
export and relocate.
**Cons:** Not a fit for the embedding index itself (vector search wants a
purpose-built structure); write concurrency is still serialised, which needs
`one connection per thread` and disciplined transaction scope to avoid lock
contention.

### Option B — Plain JSON/YAML files per entity type
**Pros:** Human-readable and diffable without tooling; trivial to hand-edit
during development.
**Cons:** No transactional guarantees across related writes (a task and its
audit event could disagree after a crash mid-write); no query language, so
every "find tasks blocked on this lock" becomes hand-rolled file scanning at
startup; concurrent writers from multiple threads need an external locking
scheme SQLite already provides for free; does not scale past a few thousand
records without becoming the bottleneck NFR-002 and NFR-003 are trying to
avoid.

### Option C — Embedded document store (e.g. TinyDB, an embedded Mongo-like store)
**Pros:** Schema flexibility during early development; nested documents map
naturally onto entities like a task with steps and checkpoints.
**Cons:** Weaker transactional and durability guarantees than SQLite in
practice; smaller, less-audited codebases for a component that the audit
trail's integrity depends on; no meaningful advantage over SQLite for this
project's access patterns, which are overwhelmingly relational (tasks ↔
locks ↔ audit events ↔ permissions).

### Option D — SQLite plus a full ORM (SQLAlchemy et al.)
**Pros:** Familiar declarative model layer; migration tooling (Alembic)
comes largely for free.
**Cons:** An ORM's session/identity-map semantics add a layer of implicit
behaviour on top of a store whose correctness is safety-critical (audit
events must never silently merge or be deduplicated by an ORM identity map);
the project's migration needs are simple enough (forward-only, versioned) that
hand-written migrations are easier to reason about and to security-review
than generated ones. Rejected for Phase 0; nothing here prevents introducing
a thin query-building layer later if hand-written SQL becomes unwieldy.

## Decision

SQLite (`jarvis.db`) is the single canonical transactional store for Project
Jarvis. Concretely:

- **WAL mode** is enabled, giving concurrent readers (GUI, audit viewer)
  alongside the scheduler's writer without blocking.
- **Foreign keys are on**, so cascading deletion of derived data (e.g.
  deleting a task deletes its steps, checkpoints and evidence records) is
  enforced by the database, not by application discipline (PRD FR-167).
- **One connection per thread.** SQLite connections are not shared across
  threads; each thread that touches the database owns its own connection.
- **Every other store is derived and rebuildable, and holds no unique
  information.** The embedding index, the file index and any cache exist
  purely as accelerators over data that also lives in SQLite; losing them
  must never lose data, only rebuild time.
- **Large or binary artefacts live on disk**, referenced by path from a
  SQLite row (screenshots, audio diagnostics, task evidence, exports,
  backups) rather than stored as BLOBs, keeping the database small, fast to
  back up, and easy to reason about.
- **Migrations are versioned and forward-only**, with an explicit registry
  and a recorded applied-at timestamp per migration. There is no down-migration
  path in Version 1; recovery from a bad migration is a restore-from-backup
  operation, not a rollback script.
- **A database newer than the running binary is a hard startup failure**, not
  a best-effort read. The schema version is checked at startup before any
  other component touches the database (PRD NFR-043).

## Enforcement

- The schema-version check runs first in `JarvisCore.start()`, before the
  event bus, audit log or any other component is constructed (see
  ARCHITECTURE.md §6.9); a mismatch where the on-disk version exceeds the
  binary's known versions raises and aborts startup rather than attempting a
  best-effort open.
- The migration registry is a single ordered list; a migration cannot be
  skipped or reordered without changing code, and each application is
  recorded with its applied-at timestamp so the current schema version is
  always derivable from the database itself.
- Integration tests exercise migrations against a fixture database and assert
  that crash recovery and audit durability survive a restart (ARCHITECTURE.md
  §11, `tests/integration/`).
- Any new store proposed as a place to hold data must be justified against
  this ADR: if it would hold information not reconstructable from `jarvis.db`,
  it is not a derived store and this decision has been violated.

## Consequences

### Positive
- One place to back up, export, relocate (PRD §14.2) or delete (NFR-025) to
  satisfy the entire durability and privacy story.
- Cascading deletion is structurally correct rather than relying on every
  call site remembering to clean up derived rows.
- Audit and task state can never silently diverge, because both are written
  in the same transactional store.

### Negative
- All writes are ultimately serialised through SQLite's single-writer model;
  under Phase 3/4 workloads (many concurrent watchers, schedules) this could
  become a throughput ceiling that a purpose-built queue would not have.
- Hand-written forward-only migrations put the burden of correctness on the
  author of each migration; there is no automated schema-diff safety net.

### Residual risk
This decision does not solve multi-device synchronisation — the vault is
explicitly single-machine, single-user. It does not solve the case where the
WAL file itself is corrupted by an abrupt power loss on a failing disk;
SQLite's WAL mode is robust but not infallible, and Version 1 has no
automatic integrity-check-and-repair path beyond restore-from-backup. It also
does not solve write contention if a future phase adds a high-frequency
writer (e.g. a per-frame audio diagnostic logger) without deliberately
batching or routing it around the primary connection.

## Revisit when
- Any phase introduces a write pattern that measurably contends with the
  scheduler's writer (candidate: Phase 3 schedules/watchers, Phase 4 folder
  watchers).
- Multi-device or cloud-sync support is ever considered — this would need a
  fundamentally different replication story, not an extension of this one.
- The embedding index needs a store with different consistency requirements
  than "just rebuild it" (e.g. if rebuild time becomes user-visible).

## Related
- ADR-0006 (configuration and vault path resolution — `VaultPaths` governs
  where `jarvis.db` lives and how it relocates).
- ARCHITECTURE.md §6.9 (runtime composition, startup ordering), §9 (data
  architecture summary), §11 (testing architecture).
- DATA_MODEL.md (full entity and schema detail).
