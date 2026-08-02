# ADR-0004: Single Process, Thread Isolation for Phases 0–3

- **Status:** Accepted, with a review trigger at Phase 3
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §12.2, §12.3, FR-004, FR-038
- **Phase:** 0

## Context

Project Jarvis's target architecture names five collaborating components:
Jarvis Shell, Jarvis Core, Audio Worker, Automation Worker and Task Scheduler
(PRD §12.2). The PRD explicitly permits these to be modules inside one
packaged application for the MVP, with one hard constraint: "audio and
automation must run outside the GUI thread. The architecture must allow them
to become separate processes without rewriting their interfaces" (PRD
§12.2).

The forces at play: process isolation is the strongest available boundary
for crash containment and privilege separation, but it also imposes real
cost — serialisation across a process boundary, IPC authentication (PRD
§12.3), separate lifecycle management, and slower iteration during a phase
where the module boundaries themselves are still being discovered. Phase 0
has no audio, no automation and no elevation to isolate yet; imposing
process separation now would be paying that cost before there is anything
concrete to protect.

## Options considered

### Option A — One process, worker threads, module boundaries as the separation (chosen)
**Pros:** Function calls and an in-process typed event bus (ADR-0005) are
cheap and simple during the phase where interfaces are still settling;
matches PRD §12.2's explicit permission for the MVP; the layering rule below
gives most of the *testing* benefit of process separation (headless
core, replaceable GUI) without the *operational* cost of it.
**Cons:** No crash containment between components; a defect in one worker
can corrupt shared in-process state or crash the whole application, taking
the GUI and every in-flight task down with it.

### Option B — Full multi-process architecture from Phase 0
**Pros:** Real crash containment and privilege separation from day one;
no later migration needed.
**Cons:** Phase 0 has no audio worker, no automation worker and nothing to
elevate — this would be building IPC authentication, token rotation and
process supervision (PRD §12.3) for components that do not exist yet,
against interfaces that are still being discovered and will likely change.
Directly contradicts PRD §12.2's "may be modules in one packaged application"
allowance for the MVP. Rejected as premature for Phase 0–3.

### Option C — Split only the highest-risk component now (automation worker) and keep the rest in-process
**Pros:** Targets isolation at the component with the largest blast radius
(desktop and browser control) earliest.
**Cons:** The automation worker does not exist in Phase 0 either — there is
nothing to isolate yet, and building process separation for a component
before its interface (`UiBackend`, ARCHITECTURE.md §8) is even stable would
mean paying the IPC cost twice. Rejected for now; this is effectively what
Option A becomes once the automation worker actually lands and its risk
profile justifies the split (see Revisit, below).

## Decision

Phases 0 through 3 run one process (`jarvis.exe`) with worker threads for
audio, automation, the task scheduler and diagnostics, plus the Qt main
thread for the GUI (ARCHITECTURE.md §4.1). Separation between components is
provided by module boundaries and typed messages, not by process boundaries.

The rule that makes this safe to promote later without a rewrite is stated
once and enforced everywhere: **`jarvis.core`, `jarvis.tasks`,
`jarvis.storage`, `jarvis.llm` and `jarvis.config` must not import
`PySide6`.** This keeps the entire engine importable and testable headlessly,
and keeps the GUI a replaceable adapter (`jarvis.ui`) rather than something
the engine's logic is entangled with — the same property a real process
boundary would give, achieved here by import discipline instead.

## Enforcement

A test (`tests/security/test_layering.py`, ARCHITECTURE.md §4.1, §5) asserts
that none of `jarvis.core`, `jarvis.tasks`, `jarvis.storage`, `jarvis.llm` or
`jarvis.config` import `PySide6`, and more generally that the layering table
in ARCHITECTURE.md §5 holds (dependencies point downward only; `jarvis.ui` is
the only package permitted to import `PySide6`). Any new import of `PySide6`
outside `jarvis.ui` fails this test (ARCHITECTURE.md §14).

## Consequences

### Positive
- Fast iteration during the phase where module interfaces are still being
  discovered: no IPC schema to version alongside the module's own logic.
- The engine is headlessly testable end to end, which is what lets
  `tests/unit/`, `tests/integration/` and `tests/acceptance/` run without a
  display or a GUI event loop.
- Promoting a component to its own process later is an implementation change
  behind an already-typed interface, not an interface redesign — the
  `TtsProvider`, `UiBackend` and similar protocols (ARCHITECTURE.md §8) are
  written as if the far side might already be a process boundary.

### Negative
- Every worker thread shares the process's memory and the Python GIL; a
  CPU-bound worker can still contend with others despite being "isolated" in
  name, and there is no OS-level scheduling fairness between them beyond
  what Python's thread scheduler provides.
- Supervision is weaker than a real process boundary: a worker thread that
  deadlocks or leaks cannot be forcibly torn down independently of the whole
  process the way a child process can be killed and restarted.

### Residual risk
**This is not a security boundary, and that must not be assumed by
anything.** ARCHITECTURE.md §13 names this explicitly as gap 2: in Phases
0–3, a defect in the automation worker can reach the vault, because both run
as threads in the same process with the same memory space and the same
filesystem access. Nothing in this ADR mitigates that; it is deferred, not
solved, and is one of the reasons the closed capability set (ADR-0003) and
the permission engine matter as much as they do — they are the controls that
still apply even though the process boundary does not.

## Revisit when

- **The Qwen3-TTS worker** is built (PRD FR-038): it already requires
  Python 3.12 and CUDA, a dependency set that conflicts with the Python 3.11
  host, so it *must* be a separate process regardless of this ADR's general
  policy, communicating over typed authenticated local IPC per PRD §12.3.
- **The elevated action helper** is built (PRD FR-004, ADR-0009): any action
  needing UAC elevation must run in a narrowly scoped helper process, never
  in the main process, because a permanently elevated main process is
  exactly the Non-Goal 2 the PRD rules out.
- **Any adapter has a conflicting dependency set** with the host process
  (mirroring the Qwen3-TTS case).
- **Phase 3, as a scheduled review.** By Phase 3 the automation worker and
  audio worker will have been running in-process for two full phases; this
  is the point at which the cost of the residual risk above should be
  re-weighed against the now-better-understood interface stability of those
  workers.

## Related
- ADR-0003 (closed capability set — the control that still applies inside
  the shared process).
- ADR-0005 (in-process typed event bus — the mechanism workers and core use
  to communicate inside this single process).
- ADR-0009 (scoped elevation via separate helper — the first component
  required to break out of this process model).
- ARCHITECTURE.md §4 (process and thread model), §5 (layering), §8
  (extension points), §13 gap 2.
- PRD §12.2, §12.3.
