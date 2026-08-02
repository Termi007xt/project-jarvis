# ADR-0024: Data retention defaults

- **Status:** Open — decision required before Phase 3 (memory, history and clipboard all persist user content)
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.14, FR-025, FR-045, FR-046, FR-166, FR-167, FR-253, FR-267, §18.5, NFR-025
- **Decision required before:** Phase 3 (Tasks, macros, and memory)

## Context

Project Jarvis accumulates several independent streams of personal data:
conversation transcripts, approved memories, an audit trail, task records,
clipboard history, notification events and diagnostic logs. Each has a different
sensitivity and a different reason to exist, so one blanket retention period
would be wrong for all of them.

Three constraints bind the answer:

1. **Every default must be user-changeable** and every stream must support
   complete deletion (PRD NFR-025).
2. **Deleting source material must offer to delete what was derived from it**
   (PRD FR-167). A retention policy that expires a conversation but leaves its
   embeddings behind is not deletion.
3. **Two streams already have fixed answers.** Raw command audio is not retained
   after transcription (FR-025) and `PROJECT_INPUTS.md` sets
   `raw_audio_retention: disabled`. Telemetry is off and opt-in (§18.5).

The tension is between usefulness and exposure. A long conversation history
makes memory retrieval better and makes "what did I ask you last Tuesday" work;
it is also the largest concentration of personal content on the machine. The
audit log pulls the other way: it is a *safety* record, and aggressively
expiring it would remove the user's ability to review what the agent did.

Phase 0 has already fixed a narrow version of this: the audit log, task records,
permission grants and runtime instances are kept until the user deletes them,
and the application log rotates at 2 MB × 3 files.

## Options considered

### Option A — Keep everything until the user deletes it

**Pros:** Simplest to implement and to explain. Never loses something the user
wanted. Maximum retrieval quality. Matches how Phase 0 already behaves.
**Cons:** Unbounded growth. The vault becomes the single richest target on the
machine (THREAT_MODEL.md, data-exfiltration group). "I deleted that months ago"
turns out to be false. Puts the entire burden of hygiene on the user.

### Option B — Per-stream defaults with expiry, all user-changeable

Each stream gets a default retention period chosen for its own purpose, surfaced
in the GUI, with a "keep forever" option per stream.

**Pros:** Proportionate. Sensitive, low-value streams (clipboard, notification
events) expire quickly; safety-relevant streams (audit) are kept. Bounded growth
without silently losing high-value data.
**Cons:** More moving parts: an expiry sweep, its own audit trail, and a rule for
what happens to derived data when a source expires. Users must understand that
different screens forget at different rates.

### Option C — One global retention period

A single "keep data for N days" setting applied to everything.

**Pros:** One control the user actually understands.
**Cons:** Wrong for every stream simultaneously. Either the clipboard is kept far
too long, or the audit log is destroyed while it is still the only evidence of
what the agent did. Conflates a safety record with a convenience cache.

## Decision

**Deferred. No option is selected yet.** Option B is the leading candidate, with
these *proposed* defaults to be confirmed before Phase 3:

| Stream | Proposed default | Rationale |
|--------|------------------|-----------|
| Conversation history | 90 days, user-changeable, disableable globally and per conversation (FR-045, FR-046) | long enough to be useful for retrieval, short enough to bound exposure |
| Approved memories | no expiry unless the memory sets one (PRD §14.4 `expires_at`) | the user explicitly approved each one |
| Memory candidates | 14 days, then discarded unrejected | a stale candidate is noise, not a decision |
| Audit log | 365 days, user-changeable, never off | it is a safety record; the user must be able to review what happened |
| Task records | 90 days after reaching a terminal state | evidence and checkpoints cascade with the task |
| Clipboard history | 24 hours, off by default (FR-253) | highest sensitivity per byte of anything on this list |
| Notification events | 30 days (FR-267) | third-party content the user did not author |
| Screenshots | per ADR-0025 (`task_only` today) | separate decision, larger disk cost |
| Raw command audio | not retained (FR-025) | already fixed |
| Diagnostic logs | 2 MB × 3 rotating files | already implemented |
| Crash logs | 30 days, local only (§18.5) | |

## Decision criteria

1. Every stream has a named default, a GUI control, and a documented reason.
2. Expiring a source offers to expire what was derived from it, and the offer is
   testable (PRD FR-167, AT-013).
3. A retention sweep is itself audited: the user can see that data was removed
   and how much.
4. No default silently deletes something the user explicitly approved (a saved
   memory, a named skill, a workspace).
5. The audit log's default is never zero and cannot be disabled entirely.
6. Total vault growth under representative daily use stays bounded — measure it
   before choosing numbers, do not guess.
7. Complete deletion of every stream is possible in one action (NFR-025).

## Consequences

### If Option B is chosen

**Positive:** Exposure is proportionate to sensitivity. Disk use is bounded. The
Memory and History screens can honestly say when something will be forgotten.
Sensitive streams default to short or off, which is the right failure mode.

**Negative:** A retention sweep is a new background job with its own failure
modes, and it must never run mid-task or delete something a running task
depends on. Cascade-on-expiry needs the same care as cascade-on-delete. Users may
be surprised that history has expired; this needs to be visible in the GUI, not
discovered.

### Deferral cost

Low through Phase 2 and rising sharply in Phase 3. Nothing before Phase 3
persists user *content* — Phase 0 and 1 hold operational records the user can
already delete wholesale. The moment conversation history, memories and clipboard
history exist, data starts accumulating under whatever rule is in force, and
retrofitting expiry to data already collected under "keep forever" means either
deleting data the user was implicitly promised, or grandfathering it and living
with two regimes. Decide this before the first Phase 3 write path lands.

## Related

- [ADR-0025-screenshot-retention.md](ADR-0025-screenshot-retention.md) — the
  largest single consumer of disk, decided separately
- [ADR-0021-encrypted-sync-and-backup.md](ADR-0021-encrypted-sync-and-backup.md)
  — what leaves the machine, if anything
- [ADR-0002-sqlite-single-source-of-truth.md](ADR-0002-sqlite-single-source-of-truth.md)
  — derived indexes must be rebuildable, which is what makes cascade deletion safe
- [DATA_MODEL.md](../../DATA_MODEL.md) §8 — retention as currently implemented
- [THREAT_MODEL.md](../../THREAT_MODEL.md) — data-exfiltration threat group
