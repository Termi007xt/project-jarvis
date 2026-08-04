# ADR-0027: Approval dialog and activation interaction model

- **Status:** Accepted (decided 2026-08-02)
- **Date:** 2026-08-02
- **Deciders:** Project owner
- **PRD reference:** §9.9, §11.2, §11.1, FR-018, FR-015
- **Phase:** 1

## Context

Phase 0 built the permission engine and the `ApprovalPort` interface, but no
dialog. The Phase 0 default implementation **denies** everything requiring
approval, so today only two self-inspection capabilities can run at all
(ADR-0010). The approval dialog is therefore the gate on every capability in
Phase 1 and beyond — nothing else can be exercised until it exists.

Three questions had to be settled before it could be built: which scopes the
dialog offers, whether a denial is remembered, and whether the dialog is modal.

The modality question is not cosmetic. A modal dialog steals keyboard focus. In
Phase 2, when Jarvis is driving another application, stealing focus mid-action
can break the very automation the user is being asked to approve, and can send
keystrokes to the wrong window.

## Decision

**1. Scope options offered.** Keep the button set small.

| Risk | Offered |
|---|---|
| Low | Allow once · Allow always · Deny |
| Medium | Allow once · Allow for this task · Deny |
| High | **Allow once · Deny** only |
| Prohibited | never reaches a dialog — denied unconditionally |

"Allow for this session" is **not** offered. It was the weakest of the four: its
lifetime is invisible to the user, and "this task" already covers the common case
of approving a multi-step operation once. The permission engine still supports
`SESSION` scope for programmatic use; the dialog simply does not offer it.

High risk offering only "Allow once" is not a UX choice — PRD §9.9 and §11.1
require fresh confirmation every time, and the engine rejects any broader
allow-grant for a high-risk capability at grant time.

**2. Denials are remembered, on request.** The dialog offers **"Don't ask again
for this application"** or **"...for this folder"** alongside Deny, when the
capability has a meaningful target. This creates a `DENY` grant scoped to
`APPLICATION` or `FOLDER`.

No engine change is needed: deny-grants already outrank allow-grants and already
short-circuit the high-risk ASK path, so a remembered denial correctly stops
Jarvis re-asking about something the user has already refused.

**3. Tray-anchored, non-modal.** The approval surface appears anchored to the
tray icon and does not take focus. Consequences that must be honoured:

- It must be **impossible to miss**: the tray icon goes to the `BLOCKED` (red)
  state while an approval is pending, and the request is listed in the Tasks
  screen with an approval control.
- It must **time out** rather than wait forever. An unanswered request expires
  and is recorded as denied-by-timeout, with the task moving to `BLOCKED` — never
  silently allowed. Silence is never consent (ADR-0010).
- Keyboard access is required (PRD NFR-030): a global "review pending approval"
  path must exist without a mouse.

**4. Push-to-talk is F9**, bare, with no modifier (PRD FR-018). Always-listening
remains the primary activation route; push-to-talk supplements it and is the
fallback before wake-word enrolment is complete (ADR-0016).

## Options considered

For modality: **modal dialog** (impossible to miss, but steals focus and can
corrupt in-flight automation), **tray-anchored non-modal** *(chosen — safe during
automation, at the cost of needing extra work to guarantee visibility)*, and
**toast notification** (rejected: Windows toasts can be suppressed by Focus
Assist and expire silently, which for an approval prompt means a request the user
never saw and cannot answer).

For scopes: the four-button set including "Allow for this session" was rejected
as one button too many, with the least comprehensible lifetime.

## Enforcement

- `tests/unit/test_tool_invoker.py` already asserts high-risk approvals offer
  `ONCE` only; extend it to assert the full offered-scope table above.
- A test must assert that an approval request that times out results in `DENIED`,
  never `ALLOW`.
- A test must assert the tray enters `BLOCKED` while an approval is pending.

## Consequences

### Positive
Fewer, clearer choices. Automation is not disrupted by focus theft. A refused
action stays refused without nagging. The engine already supports all of it, so
this is UI work rather than a permission-model change.

### Negative
Non-modal means visibility must be engineered rather than assumed — tray state,
task list entry, and timeout all have to work, and each is a place to get it
wrong. A missed approval looks to the user like Jarvis silently ignoring them.

### Residual risk
"Don't ask again for this application" is a durable, broad grant created in a
single click at exactly the moment the user is irritated. The Permissions screen
must make these easy to find and revoke, or they will accumulate unnoticed.

## Revisit when
Users report missing approval requests (which would argue for modality for
high-risk actions specifically), or the offered-scope set proves too coarse in
practice.

## Related
ADR-0010 (honest degraded UI — the deny-by-default port this replaces),
ADR-0016 (wake-word enrolment — push-to-talk as fallback),
ADR-0028 (barge-in), PRD §9.9, §11.1, §11.2, FR-018.
