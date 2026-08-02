# ADR-0009: Scoped Elevation via a Separate Helper Process

- **Status:** Accepted (policy); implementation Deferred
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** FR-003, FR-004, FR-079, FR-238, §12.3, NFR-020
- **Phase:** 0

## Context

Project Jarvis runs without administrator rights by default (PRD FR-003,
NFR-020), and the PRD's Non-Goal 2 rules out running the full application
permanently as administrator under any circumstance. At the same time, some
genuinely legitimate Windows actions require elevation — certain settings
changes, certain installs — and the PRD does not pretend those needs will
never arise; instead it specifies exactly how they must be handled when they
do: "When an action genuinely requires elevation, Jarvis shall use a
separate, narrowly scoped elevated helper and display the exact action
before Windows UAC appears" (PRD FR-004). Settings changes that need
elevation are explicitly routed through this same policy rather than
inventing a parallel path (FR-238).

A second, related constraint shapes the design: Jarvis must never interact
with the Windows secure desktop or UAC prompts themselves (FR-079). The
secure desktop exists precisely so that the process requesting elevation
cannot also control or spoof the consent prompt; anything that tried to
would defeat the purpose of UAC entirely. This rules out any design where
Jarvis auto-clicks, monitors, or otherwise touches the UAC dialog.

Nothing in Phases 0 through 2 is known to require elevation — Phase 0 has no
computer-control capability at all, and the currently planned Phase 1/2 tool
set (application launching, browser automation, deterministic desktop
automation) does not touch anything that needs administrator rights. This
ADR therefore records a policy decision now, while there is no concrete
elevation need to build against, so that the moment one appears it is
implemented against an already-reviewed design rather than improvised.

## Options considered

### Option A — No elevation at all in Version 1
**Pros:** Simplest possible position; removes an entire category of risk
from the product; forces every feature request that would need elevation to
be either redesigned to avoid it or explicitly deferred.
**Cons:** Some legitimate, low-risk actions genuinely require elevation on
Windows (certain settings pages, some installer flows) and permanently
excluding them narrows the product more than the PRD intends — FR-004 exists
precisely because the PRD anticipates this need rather than ruling it out.
Rejected as more restrictive than the PRD requires, though it is
functionally where Phase 0–2 sit today by simple absence of any elevation
need.

### Option B — An on-demand elevated helper, launched per action (chosen policy)
**Pros:** Matches FR-004 exactly: a separate, narrowly scoped process
performs exactly one declared action, requested fresh each time, with the
action displayed before the real Windows UAC prompt appears — so the user
sees what Jarvis is asking Windows to elevate before Windows asks them to
approve it. The helper's lifetime is bounded to the single action, which
minimises the window during which anything is running elevated at all.
**Cons:** Per-action process launch has real latency and complexity
(spawning a process, establishing authenticated IPC per PRD §12.3, waiting
for UAC, tearing the helper down again) compared to a long-lived elevated
component — but that complexity is the direct cost of the safety property
this ADR exists to preserve, not an accident.

### Option C — A persistent elevated service
**Pros:** Would avoid the per-action launch latency and IPC setup cost of
Option B; a Windows service already running elevated could service
elevation requests instantly.
**Cons:** Rejected outright. A persistent elevated service is, in effect,
"the application runs as administrator all the time" wearing a service
manifest instead of a process token — it is precisely the Non-Goal 2
scenario the PRD excludes, just moved into a component that happens not to
be the main GUI process. It also enlarges the attack surface permanently:
any defect in the service, or any way to reach it from the unprivileged main
process (which, per ADR-0004, shares a process with several worker threads
in Phases 0–3), is now a standing elevation-of-privilege path rather than
one that exists only for the seconds a specific approved action takes.

## Decision

**The application never runs permanently as administrator.** When an action
genuinely requires elevation, a separate, narrowly scoped helper process
performs exactly that one action — nothing else, no generic elevated
execution capability — and the exact action Jarvis is about to ask Windows
to elevate is displayed to the user before the Windows UAC prompt appears
(FR-004, FR-238). Jarvis never interacts with the Windows secure desktop or
the UAC prompt itself (FR-079): the user's consent is given to Windows
directly, on Windows' own trusted surface, not mediated or observed by
Jarvis in any way.

Because nothing in Phases 0–2 is known to require elevation, **the helper is
not built yet.** This ADR accepts the policy — no permanent elevation, a
scoped per-action helper is the only acceptable shape for elevation when it
is needed — while deferring the implementation until a concrete action
requires it.

When the helper is built, its IPC must follow PRD §12.3: bind only to a
loopback address or a Windows named pipe, generate a per-installation
authentication token, expose no unauthenticated network port, reject
requests from non-local interfaces, and rotate the token during reset. This
is the same IPC discipline required of any process-separated component
(ADR-0004), applied here to the highest-privilege component the product
will ever run.

## Enforcement

- There is no elevation manifest and no elevated code path anywhere in
  Phase 0–2, which ARCHITECTURE.md's testing architecture names explicitly:
  the security suite includes a check for "no elevation manifest"
  (ARCHITECTURE.md §11). Its presence would be a direct signal that this
  policy has been violated.
- The single-instance guard and the main process both run `asInvoker`
  (ARCHITECTURE.md §6.9); nothing in the packaging or manifest requests
  elevation for the main executable.
- When the helper is eventually introduced, its scope (the one action it
  performs) must be declared and reviewed the same way a tool's `ToolSpec`
  is declared and reviewed (ADR-0003) — a helper that grows a second
  capability without a fresh review is a structural regression of this ADR,
  not a minor addition.
- Any code path that would make Jarvis observe, screenshot, or interact with
  the secure desktop or a UAC dialog is a violation of FR-079 regardless of
  intent (e.g. "just to confirm it appeared") and must be rejected in
  review.

## Consequences

### Positive
- The overwhelming majority of Jarvis's runtime — everything except the
  bounded lifetime of a helper process performing one declared action —
  never holds elevated rights, which is the strongest practical mitigation
  against a defect (in the LLM-directed planner, in a tool, in the
  automation worker) translating into system-level compromise.
- Users see the exact action before Windows' own consent surface appears,
  which is strictly more transparent than a bare UAC prompt alone would be,
  without Jarvis touching that surface.

### Negative
- Every elevation-requiring feature costs more to build than it would under
  a persistent-service design: a helper binary, an IPC contract, a token
  lifecycle, and a UI flow to show the pre-UAC explanation, all before the
  feature itself does anything.
- Latency: launching a helper process and waiting on UAC is inherently
  slower than a call into an already-running elevated component. This is an
  accepted cost of the policy, not an oversight.

### Residual risk
This does not solve elevation requests that a user approves without reading
the pre-UAC explanation carefully — the design gives the user better
information than a bare UAC prompt, but cannot force them to use it. It also
does not yet have an implementation to evaluate: because the helper is
deferred, its actual IPC authentication, token rotation and process
supervision have not been built or reviewed, and this ADR's guarantees are
currently a policy commitment rather than a tested property of running code.

## Revisit when
Any concrete action in the backlog is found to require elevation — the
trigger is the first real feature, not a phase number. At that point the
helper's design (IPC transport, token format and rotation, the exact UI for
the pre-UAC explanation, and the helper's own narrow `ToolSpec`-equivalent
declaration) must be written up and reviewed before the feature ships, and
this ADR's status should move from "implementation Deferred" to reflect the
helper's existence.

## Related
- ADR-0003 (closed capability set — the same "narrowly scoped, reviewed,
  no generic capability" discipline applied to the highest-privilege
  component).
- ADR-0004 (single-process thread isolation — the elevated helper is named
  there as one of the two known triggers for process separation).
- ARCHITECTURE.md §4.2 (later-phase process separation), §11 (testing
  architecture — elevation manifest check).
- PRD §12.3 (local communication requirements for separate processes).
