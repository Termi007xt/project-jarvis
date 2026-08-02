# ADR-0025: Maximum screenshot retention

- **Status:** Accepted for the default (`task_only`); the diagnostic ceiling and disk bound remain Open — decision required before Phase 4
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.15, FR-073, FR-271, FR-272, FR-273, FR-278, FR-279, NFR-006
- **Decision required before:** Phase 4 (vision fallback produces screenshots at volume)

## Context

Screen captures are the highest-risk artefact the product will ever write to
disk. A single screenshot can contain an authentication code, a bank balance, a
private message, or a password manager mid-reveal — content the user never
consented to store and, in some cases, content belonging to somebody else.

They are also unavoidable once Phase 4 arrives: vision fallback (FR-074) needs an
image to reason about, and every visual action must be verified against a
post-action state (FR-075, FR-276). Verification evidence is what makes the
honesty requirement enforceable rather than aspirational.

`PROJECT_INPUTS.md` already sets `screenshot_retention: task_only`, and
`config/defaults.yaml` carries it. PRD FR-278 defines four modes: no retention,
retain until task completion, retain for diagnostics, retain selected only.

Two constraints are already fixed and not in question:

- Capture is scoped to the narrowest sufficient target — control, then window,
  then region, then monitor; full desktop only with approval (FR-271).
- Users may block capture entirely for named applications, and Jarvis must refuse
  rather than capture them (FR-273, AT-031).
- Capture must be visibly indicated while it happens (FR-272).
- Screenshots are excluded from normal exports (FR-279).

Phase 0 writes no screenshots at all; `attachments/screenshots/` exists but stays
empty. What is genuinely undecided is the *ceiling*: how long diagnostic
retention may last, and how much disk it may consume before something gives.

## Options considered

### Option A — `task_only` default, hard delete at task completion

Screenshots live only as long as the task that produced them, and are deleted
when it reaches a terminal state, regardless of outcome.

**Pros:** Smallest exposure window. No accumulation. Matches the already-selected
input. Simple to reason about and to explain.
**Cons:** A failed task's evidence disappears exactly when the user most wants to
see why it failed. Debugging a flaky automation becomes guesswork.

### Option B — `task_only` default, with retention extended for failed tasks

As Option A, but screenshots attached to a task that ended `failed` or `blocked`
survive for a bounded period so the user can inspect the failure.

**Pros:** Keeps the evidence that is actually useful. Successful tasks — the vast
majority — still leave nothing behind. Aligns retention with the honesty
requirement: a task claiming failure should be able to show why.
**Cons:** Failure is correlated with unusual screen states, which is exactly when
a screenshot is most likely to have caught something unexpected. Needs the same
sensitive-application exclusions applied at retention time, not just capture time.

### Option C — Diagnostic mode with a global disk budget

Retention becomes a user-chosen mode; diagnostic mode keeps everything up to a
byte ceiling, evicting oldest-first.

**Pros:** Bounded disk regardless of behaviour. Gives a power user a real
debugging tool when they explicitly ask for one.
**Cons:** Oldest-first eviction is not risk-aware — it can retain a sensitive
capture while discarding a harmless one. A disk budget is not a privacy control,
and presenting it as one would be misleading.

## Decision

**Accepted for the default:** `task_only`, as already configured. Screenshots are
temporary by default (FR-278), attached to the task that produced them, and
deleted when it reaches a terminal state.

**Open, to be decided before Phase 4:**

1. Whether failed and blocked tasks get an extended window (Option B), and how
   long — a proposed 7 days, to be confirmed.
2. The absolute ceiling for `diagnostic` mode: a proposed 500 MB and 14 days,
   whichever binds first, to be confirmed against measured capture sizes.
3. Whether `selected` mode requires a fresh per-screenshot confirmation or a
   single session-scoped approval.

## Decision criteria

1. A screenshot from a blocked-capture application is never written to disk at
   all — the exclusion is enforced at capture time, not at display time (FR-273,
   AT-031).
2. Retention never exceeds the mode's stated bound, and the bound is visible in
   the GUI alongside current disk use (NFR-006).
3. Deleting a task deletes its screenshots, verifiably, with no orphans left in
   `attachments/screenshots/`.
4. Screenshots never appear in a normal export, and the export test proves it
   (FR-279).
5. Diagnostic mode requires an explicit opt-in, states plainly what will be kept
   and for how long, and reverts to the default when disabled.
6. Measured: typical capture size at the target resolution, and capture rate
   during a representative Phase 4 vision task. Choose the ceiling from that, not
   from a guess.
7. A screenshot referenced as task evidence is either retained for as long as the
   evidence claim stands, or the evidence records that the image has expired —
   never a dangling path presented as if it were viewable.

## Consequences

### If the default plus Option B is chosen

**Positive:** Successful automation leaves no image trail, which is the common
case and the right default. Failure remains diagnosable. Disk use stays
negligible in normal operation. The privacy story is simple enough to state in
one sentence in the GUI.

**Negative:** Failed-task screenshots are the most likely to have captured an
unexpected screen state, so the extended window carries disproportionate risk and
needs the sensitive-application exclusion applied rigorously. Deleting a
screenshot referenced by task evidence requires the evidence record to degrade
gracefully rather than point at a missing file.

### Deferral cost

Low until Phase 4, because nothing captures the screen before then. The cost is
concentrated at one point: the first Phase 4 capture must already know its
retention rule, because a screenshot written under an undecided policy is a
screenshot with no deletion schedule. Decide the ceiling before the first
`capture_window` call ships, not after.

## Related

- [ADR-0024-data-retention-defaults.md](ADR-0024-data-retention-defaults.md) —
  the other retention streams
- [ADR-0010-honest-degraded-ui-over-fake-functionality.md](ADR-0010-honest-degraded-ui-over-fake-functionality.md)
  — evidence that has expired must say so rather than appear viewable
- [SECURITY.md](../../SECURITY.md) — screen capture controls and exclusions
- [THREAT_MODEL.md](../../THREAT_MODEL.md) — privacy threat group: capture of a
  password manager or banking application
- [DATA_MODEL.md](../../DATA_MODEL.md) §8 — retention as currently implemented
