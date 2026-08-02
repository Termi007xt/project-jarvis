# ADR-0010: Honest Degraded UI Over Fake Functionality

- **Status:** Accepted
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §1 item 10, §4.6, §9.2, §9.3, FR-048
- **Phase:** 0

## Context

Project Jarvis is being built incrementally, phase by phase (PRD §21), which
means for most of the project's life the running application will have
navigation areas, menu items and capabilities that do not exist yet sitting
alongside ones that do. How the product presents that gap is a genuine
design decision with architectural consequences, not just a cosmetic one.
The PRD sets the standard directly: instruction 10 to the implementation
agent is "Avoid placeholders, fake implementations, silent failures, or
success messages that are not supported by verified outcomes" (PRD §1.10),
and product principle §4.6 states it as a hard rule about status reporting:
"Jarvis may only report a task as completed after its success criteria have
been verified. 'I clicked it' is not equivalent to 'the task succeeded.'"
FR-048 makes the same demand of the runtime: "Jarvis shall never claim an
application action completed unless a tool or verification step confirms
it."

This is not only a UI-copy question. If the standard is "never claim success
that was not verified", then the moment a feature does not exist, the
system must have some behaviour for it that is not success — and the two
easy ways to get that wrong are worth naming: hiding the feature so its
absence in Phase 0 looks like it was never planned, or wiring it to a stub
that quietly does nothing and says "done" anyway. Both violate the standard
above; the second one violates it more directly, because it manufactures
exactly the fake success message PRD §1.10 prohibits.

## Options considered

### Option A — Show unavailable features, disabled, with a tooltip naming the phase (chosen)
**Pros:** The tray menu (PRD §9.2) and the main window's fifteen navigation
areas (PRD §9.3) show the product's real shape from Phase 0 onward — a user
or reviewer can see what Jarvis is *for*, not just what it currently does;
disabling with an explanatory tooltip is honest about the gap without
pretending the gap does not exist; it also gives phase progress a visible,
checkable signal (a nav item moving from disabled to enabled is direct
evidence a phase landed).
**Cons:** A user opening the app in Phase 0 sees more disabled controls than
working ones, which could read as unfinished or broken to someone unfamiliar
with the phased delivery plan, if the tooltip explanation is not good
enough to carry that context on its own.

### Option B — Hide unavailable features entirely until they ship
**Pros:** The UI only ever shows what works, which reads as more polished at
any given snapshot in time.
**Cons:** Rejected. It hides the product's actual shape — someone cannot
tell from the running application what Jarvis is meant to become, only what
it currently does — and it makes phase progress invisible rather than
observable: a feature "shipping" is not a visible event in the UI, it is a
silent appearance of a menu item that previously did not exist. This works
against the same transparency PRD §1.10 is protecting on the status-message
side; it is just applied to product surface instead of task outcomes.

### Option C — Stub unavailable features with a "coming soon" toast or a fake success path
**Pros:** None found that outweigh the cons; superficially it might feel
more "complete" to click something and get a response rather than a
disabled control.
**Cons:** Rejected outright. This is still a fake code path — clicking
"Skills" and getting a toast that says "coming soon" is materially the same
category of thing as a tool that reports success without verification: a
response manufactured to seem like a real answer to the user's action rather
than an honest statement that the action cannot be performed yet. PRD §1.10
prohibits exactly this.

## Decision

Tray menu items and main-window navigation areas for features that do not
exist yet are shown but **disabled, with a tooltip naming the phase** they
belong to, rather than hidden or wired to a stub that reports success. Phase
0 implements Home, Tasks, Permissions, Audit log, Settings and About against
live data; the remaining navigation areas render an honest "not implemented,
Phase N" panel rather than being hidden or faked (ARCHITECTURE.md §6.10).

This principle has architectural consequences beyond the UI layer, because
"never claim unverified success" has to be true everywhere the possibility
of a fake-success path could exist, not only in the tray:

- **The Phase 0 `ApprovalPort` default implementation denies rather than
  auto-approving.** `ApprovalPort` is an interface the core asks and the
  shell answers (ARCHITECTURE.md §6.6); Phase 0 has no approval dialog
  built yet, so the default implementation — `DenyingApprovalPort` — refuses
  every request that reaches it. A capability requiring approval simply
  cannot run until a real dialog exists to ask the user. **Silence is never
  consent.**
- **`ToolResult` distinguishes `succeeded` from `unverified`.** A tool that
  cannot verify its own effect reports `unverified`, and the task layer
  treats that as not-succeeded (PRD FR-048, AT-018) — there is no boolean
  "worked" a tool can set to paper over the absence of real verification.
- **Tray icons are drawn programmatically with `QPainter` rather than
  shipped as image assets.** This is a smaller, more literal instance of the
  same "do not fake what you do not have" discipline: rather than shipping
  placeholder artwork now and swapping it for a licensed or original icon
  set later — which risks the placeholder quietly becoming the shipped
  product — the tray renders its seven states (PRD §9.1) programmatically,
  which also sidesteps the asset-licensing constraint in PRD §17.3 (no
  third-party icon set without redistribution rights) until an original set
  exists.

## Enforcement

- `DenyingApprovalPort` as the default binding means any capability whose
  risk level requires `ASK` (ARCHITECTURE.md §6.4) structurally cannot
  execute until a real `ApprovalPort` is wired in — this is enforced by the
  permission evaluation order itself, not by a separate check that could be
  forgotten.
- `ToolResult`'s outcome enum (`succeeded`, `failed`, `denied`, `blocked`,
  `timed_out`, `cancelled`, and the `unverified` distinction within
  `succeeded`) is a typed contract every tool must satisfy; a tool cannot
  report success through an untyped or boolean channel that would bypass
  this distinction.
- Disabled navigation items and their phase-naming tooltips are covered by
  the UI test suite (`tests/ui/`, ARCHITECTURE.md §11), run under
  `QT_QPA_PLATFORM=offscreen`, so a feature accidentally left enabled ahead
  of its phase — or a phase-N item that ships without ever being re-enabled
  — is a visible test change, not a silent drift.
- Any new tool implementation is reviewed against whether its declared
  verification method (PRD §13.2) is real and sufficient, not decorative;
  this is a review-time discipline this ADR names explicitly rather than a
  fully automatable check.

## Consequences

### Positive
- The product's real shape and real phase progress are both directly
  observable in the running application at every point in development, which
  is valuable both to the project owner tracking progress and to any future
  reviewer or contributor.
- "Success" means the same thing everywhere in the system — verified — which
  removes an entire class of bug where a feature *looks* done because it
  returns a friendly result that was never actually checked.
- The `DenyingApprovalPort` default means Phase 0 cannot accidentally expose
  a medium- or high-risk capability before there is a real UI for the user
  to say yes or no to it — the safe failure mode is the only failure mode.

### Negative
- A Phase 0 build genuinely looks sparse: six live navigation areas out of
  fifteen, most tray menu affordances present but inert. This is a real cost
  to first impressions that Option B would have avoided, accepted here in
  exchange for honesty about progress.
- Disabled-with-tooltip requires each unimplemented area to carry accurate,
  well-written phase information — a vague or stale tooltip ("not yet
  available") gives back some of the transparency this decision is meant to
  provide.

### Residual risk
This does not solve the risk of a tooltip or "not implemented" panel going
stale — naming "Phase 2" in a tooltip is only honest if that number is kept
current as the roadmap shifts; nothing currently checks tooltip phase labels
against PRD §21's phase definitions automatically. It also does not solve
verification quality: `ToolResult.unverified` correctly refuses to claim
false success, but a tool whose declared verification method is weak (checks
something only loosely correlated with the real effect) can still produce a
`succeeded` result that is technically verified but not actually trustworthy
— this ADR enforces the *category* distinction, not the *quality* of every
tool's verification logic.

## Revisit when
- A real `ApprovalPort` (Qt dialog) ships in Phase 1 — at that point
  `DenyingApprovalPort` becomes the headless/test/offline fallback rather
  than the only implementation, and this ADR's "silence is never consent"
  property should be re-verified against the real dialog's behaviour
  (e.g. dismissing the dialog without a choice must still resolve to deny,
  not to a default allow).
- An original icon set exists (PRD §17.3), at which point programmatic
  `QPainter` tray icons may be replaced — deliberately, not as a shortcut
  taken under release pressure.

## Related
- ADR-0003 (closed capability set — the same "no fake capability" discipline
  applied to tool existence rather than tool outcome reporting).
- ARCHITECTURE.md §6.6 (tool invoker, `ApprovalPort`, `ToolResult`), §6.10
  (shell and tray), §10 (error handling, timeouts and honesty), §12 (what
  exists in Phase 0).
- PRD §9.1 (tray states), §9.2 (tray menu), §9.3 (main window navigation
  areas), §17.3 (asset licensing constraint).
