# ADR-0005: An In-Process Typed Event Bus

- **Status:** Accepted
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §1 item 9, §12.2, NFR-003, NFR-041
- **Phase:** 0

## Context

Every component described in ADR-0004 needs to tell the rest of the system
what just happened without being coupled to who is listening: the task
scheduler needs to announce a state transition, the permission engine needs
to announce a decision, and both the audit log and the GUI need to hear
about nearly everything without either of them being wired directly into the
components that produce these facts. The PRD requires typed interfaces and
structured messages throughout the core (PRD §1 item 9, NFR-041), and
requires the GUI thread to stay responsive regardless of what is happening on
worker threads (NFR-003) — so whatever carries these notifications across
threads must not risk blocking the publisher on a slow subscriber, and must
not let one broken subscriber take down the audit trail or the rest of the
system.

Because Phase 0–3 run as one process with several threads (ADR-0004), this
does not need to be a distributed messaging problem. It needs to be a
same-process, cross-thread notification problem, solved with the smallest
mechanism that actually fits that problem — not one borrowed from a
different scale of system.

## Options considered

### Option A — In-process typed publish/subscribe bus (chosen)
**Pros:** Events are frozen pydantic models, so every event is schema-typed
and self-describing; subclass matching means a handler can subscribe to the
base `Event` type and see everything, or to `TaskStateChanged` and see only
that, without a routing-key convention to keep in sync; publish is
thread-safe by construction, so any worker thread can publish without
coordinating with others.
**Cons:** It is only as durable as the process — a crash between publish and
handling loses the notification (acceptable here, because anything requiring
durability is expected to go through the task store instead, not the bus).

### Option B — Qt signals and slots throughout
**Pros:** Native to PySide6, well understood, automatic thread-affinity
handling via queued connections.
**Cons:** Would require `jarvis.core` and every capability module to import
`PySide6` to define or emit signals, directly violating the layering rule in
ADR-0004 that keeps the engine headlessly testable. Rejected: it couples the
domain model to a specific GUI toolkit for no benefit the toolkit actually
provides here.

### Option C — asyncio queues / an asyncio event loop per consumer
**Pros:** Good fit if the whole system were already asyncio-native.
**Cons:** Project Jarvis's core is thread-based (ADR-0004), not
coroutine-based; adopting asyncio queues would force every consumer —
including simple, synchronous ones like the audit log — to either run inside
an event loop or bridge across the sync/async boundary themselves. That is
extra machinery imposed on the simplest consumers to serve the needs of
none of them yet. Rejected for Phase 0; nothing here rules out an asyncio
integration point later (e.g. `qasync`, per PRD §12.1) at the Qt boundary
specifically.

### Option D — A real message broker (embedded or external)
**Pros:** Persistence, retry, delivery guarantees, cross-process readiness
out of the box.
**Cons:** Every one of those properties is solving a problem Project Jarvis
does not have inside a single process: there is nothing to retry (a lost
in-process notification is not the record of truth — SQLite is, per
ADR-0002), and there is no cross-process consumer yet (ADR-0004). Rejected as
unjustified complexity for a single-process system.

## Decision

Project Jarvis uses an in-process publish/subscribe bus (`jarvis.core.events`)
carrying frozen pydantic events. Every event derives from a common `Event`
base carrying `event_id`, `occurred_at` and `source`; subscribers match by
subclass, so a subscriber to `Event` sees everything and a subscriber to
`TaskStateChanged` sees only that. Publishing is thread-safe: any thread may
publish. Handlers run synchronously on the publishing thread, and a handler
that raises is caught, logged and isolated — it never breaks the publisher or
any other subscriber. This matters concretely because the audit log and the
GUI bridge are both subscribers, and a defect in one must never silence the
other.

The bus is deliberately **not** a message broker: it has no persistence, no
retry, and no cross-thread ordering guarantee beyond "handlers for a given
publish call run before that publish call returns, on the publishing
thread". Anything that needs durability — the fact that a task transitioned,
the fact that a tool ran — goes through the task store and audit log
directly, not through the bus as its system of record; the bus is how other
components find out about it, not where the fact lives.

The GUI never subscribes to the bus directly. `jarvis.ui.qt_bridge.EventBridge`
subscribes once, on behalf of the whole UI layer, and re-emits every event as
a queued Qt signal. This is the single place where the domain's threading
model (any thread may publish) and Qt's threading model (only the main
thread may touch widgets) meet, and it is the only such place — no other
component reaches across that boundary.

## Enforcement

- The "GUI never subscribes directly" rule is a consequence of the layering
  rule in ADR-0004: since only `jarvis.ui` may import `PySide6`, and Qt
  widgets can only safely be touched from the Qt main thread, any direct
  subscription from outside `EventBridge` would either fail the layering
  test or introduce a cross-thread widget access bug — both are caught by
  the existing test and by code review, not by a bespoke check.
- Handler isolation (a raising subscriber cannot break the publisher or other
  subscribers) is a property of the bus's publish loop itself — the loop
  catches and logs per-handler, rather than letting an exception propagate
  out of `publish()` — and is covered by the project's unit-test suite
  (ARCHITECTURE.md §11).
- Any component found publishing what is actually durable state (rather than
  a notification about durable state already written elsewhere) through the
  bus alone, with no corresponding row in `jarvis.db`, is a violation of
  ADR-0002 and should be treated as a bug, not a design choice.

## Consequences

### Positive
- Producers and consumers are decoupled by type, not by naming convention or
  registration order; adding a new subscriber to an existing event requires
  no change to the publisher.
- The audit log's reliability does not depend on the GUI being present or
  well-behaved, and vice versa, because each is an independent subscriber
  with isolated failure.
- Because events are pydantic models, they are automatically covered by the
  same schema-typing discipline as the rest of the core (NFR-041).

### Negative
- Handlers running synchronously on the publishing thread means a slow
  handler *does* block that publisher until it returns — the isolation
  guarantee covers exceptions, not latency. A handler doing meaningful work
  must offload it rather than doing it inline.
- Because there is no persistence or replay, a subscriber that is not yet
  constructed when an early event fires (e.g. `AppStarted`) simply never
  sees it; startup ordering in `JarvisCore.start()` has to construct
  subscribers before the events they care about can occur.

### Residual risk
This does not solve cross-process eventing. The moment any component is
promoted out of this process (ADR-0004's Qwen3-TTS worker or elevation
helper), it can no longer be a bus subscriber or publisher in this sense —
it needs its own typed authenticated IPC channel (PRD §12.3), and something
in-process has to bridge that channel onto the bus on its behalf. That
bridging is not designed yet.

## Revisit when
- The first component is promoted to a separate process (ADR-0004's
  triggers) and needs its notifications to reach in-process subscribers.
- A slow handler is found to measurably affect publisher latency in
  practice, which would motivate an explicit "fire and offload" pattern
  rather than synchronous handler execution.

## Related
- ADR-0004 (single-process thread isolation — the reason a broker is
  unjustified today).
- ADR-0002 (SQLite as source of truth — what durability actually goes
  through, instead of the bus).
- ARCHITECTURE.md §6.2 (typed event bus), §6.10 (`EventBridge`), §7 (control
  flow), §11 (testing architecture).
