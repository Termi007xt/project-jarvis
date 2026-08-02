# ADR-0023: Adapter Isolation

- **Status:** Open — decision required before Phase 2
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.13, FR-150, NFR-040; also ARCHITECTURE.md §13 gap 2, §8
- **Decision required before:** Phase 2 (first real application adapters ship: Brave, YouTube, Xbox; the Automation Worker becomes load-bearing)

## Context

NFR-040 requires application integrations be modular. FR-150 requires the architecture support adapters for agentic development tools, beginning with Google Antigravity. ARCHITECTURE.md §8's extension-point table already defines the `AppAdapter` interface (launch, verify, close, actions) with Brave, YouTube, Xbox, and Antigravity as its first consumers across Phases 2 and 5, and states plainly: "Adapters are in-process today. Whether they become isolated plugins is an open decision" — this ADR is that decision's formal record. ARCHITECTURE.md §13 gap 2 names the concrete cost of deferring it: "In-process isolation is not a security boundary. In Phases 0–3 a defect in the automation worker can reach the vault." §4.1's process model confirms the current design: shell, core, scheduler, and workers run inside one Windows process, separated only by module boundaries and typed messages, "so that promoting a component to its own process later requires no interface change" — the architecture was deliberately built so this decision stays cheap to revisit, not so it never needs revisiting.

**Numbering note:** ARCHITECTURE.md currently cross-references this same decision under two different placeholder numbers — §13 gap 2 cites "ADR-0004" and §8's extension-point table cites "ADR-0010." Both fall in the 0002–0010 range reserved for other use and are not used here; this document, ADR-0023, is the actual record PRD §25.13 asks for. ARCHITECTURE.md's cross-references should be reconciled to point here when that document is next revised; that reconciliation is out of scope for this ADR, which must not modify ARCHITECTURE.md.

The security argument ARCHITECTURE.md gestures at is concrete: application adapters and the Automation Worker they run inside are the components most exposed to untrusted, adversarial input — screen content, DOM content, and UI Automation trees are all things a third-party application (or a malicious website rendered inside the dedicated Brave profile, ADR-0019) partially controls. §11.4's prompt-injection defence wraps this content as untrusted *data* at the planning-and-tool-call layer, protecting against the model being tricked into proposing a bad tool call — it does not protect against a defect in an adapter itself (a parsing error, an unvalidated selector) being triggered by crafted content to do something the adapter's code was never asked to do. In-process, such a defect runs with the same privileges as `jarvis.core` and `jarvis.storage`, which sit in the same process as the vault; a process boundary would contain the defect's blast radius to the worker, unable to directly touch the database file or in-process secret material even if it went wrong.

## Options considered

### Option A — Remain in-process (status quo through Phase 2, revisit later)
Continue the current architecture: adapters and the Automation Worker run as threads/modules inside `jarvis.exe`, separated by typed interfaces and the L1–L5 layering ARCHITECTURE.md §5 enforces via tests, but not by an OS process boundary.
**Pros:** zero migration cost right now; matches ARCHITECTURE.md's stated design intent (Phase 0–3 is deliberately single-process per §4.1); avoids the IPC/serialization/authentication overhead §12.3 would otherwise require; keeps development velocity high while the `AppAdapter` interface itself is still being iterated on.
**Cons:** the security gap ARCHITECTURE.md §13 gap 2 already names persists through however many phases Option A is retained; a crash in one adapter can, at minimum, destabilise the whole process even before considering a deliberate exploit; dependency conflicts between adapters have no isolation to fall back on.

### Option B — Isolated plugin processes per adapter
Each `AppAdapter` runs in its own process, communicating with `jarvis.core` over the typed, authenticated local IPC §12.3 and ARCHITECTURE.md §4.2 already specify for the Qwen3-TTS worker and any future elevated-action helper.
**Pros:** the security boundary becomes real, not aspirational — a compromised or crashing adapter cannot directly read `jarvis.db`, in-process secret material, or other adapters' state; crash isolation improves reliability (one misbehaving adapter does not take down the tray, scheduler, or unrelated running tasks); dependency conflicts between adapters become a non-issue; this is the same pattern already accepted for the Qwen3-TTS worker (FR-038) and anticipated for the elevated-action helper, so it is not a novel pattern for this codebase.
**Cons:** real engineering cost — every `AppAdapter` call becomes a cross-process call needing schema validation, timeouts, and authentication rather than a plain call; the permission engine and audit log (§6.3, §6.4) need to correctly attribute actions taken by a separate process back to the originating task; process-per-adapter multiplies running processes, with memory/startup overhead that matters more on lower-spec hardware than the reference machine.

### Option C — Isolated processes only for the highest-risk adapters
A middle ground: keep low-risk, well-understood adapters (e.g. simple "open approved application," "open approved website" from the Low-risk class, §11.1) in-process, but isolate adapters that inherently touch high-risk surfaces — browser automation in a logged-in profile (ADR-0019's live-session concern), and IDE adapters that must never auto-approve terminal commands or credential access (FR-154).
**Pros:** concentrates the isolation cost where the security argument is strongest, avoiding Option B's full IPC overhead for comparatively low-risk adapters; a defensible, risk-proportionate use of engineering effort.
**Cons:** requires a defensible, maintained classification of which adapters are "high enough risk" to isolate — a classification that can drift as adapters gain capabilities over time; two different adapter execution models is arguably more total complexity to maintain correctly than one consistent model, even if the isolated subset is smaller.

## Decision

Deferred. No option is selected yet. Option A (in-process) is the correct posture through Phase 0–1, since ARCHITECTURE.md §4.1 already commits to this and no adapters exist yet to isolate; the decision must close before Phase 2, when the first real adapters and the Automation Worker itself become load-bearing and start processing genuinely untrusted content.

## Decision criteria

1. Whether the `AppAdapter` interface has stabilised enough by the time Phase 2 begins that the IPC/serialization cost of Option B is not fighting a still-changing contract.
2. A measured crash/defect rate from early Phase 2 adapter development — if in-process adapters demonstrably destabilise the whole process during development, that is direct evidence favouring B/C sooner rather than later.
3. Whether ADR-0012 (shell technology) selects a native shell with Python sidecars — if so, the IPC infrastructure Option B needs is being built anyway, substantially lowering B's marginal cost.
4. For Option C: a concrete, written classification of which adapters are high-risk-enough to isolate, reviewed whenever an adapter's declared `required_permissions`/risk category changes, tied to the same risk-level data ARCHITECTURE.md §6.4's capability catalogue already tracks.
5. Measured overhead (latency, memory) of Option B's IPC path against Option A's in-process calls, at actual automation call frequency, to confirm compatibility with NFR-013's timeout expectations and the "responsive UI" driver (ARCHITECTURE.md §2 driver 4).

## Consequences

### If Option A (in-process) continues through Phase 2 and beyond
Fastest adapter development velocity, but ARCHITECTURE.md §13 gap 2's named risk persists into the phase where it first becomes concretely exploitable (real web content, real third-party UI trees). An acceptable Phase 0–1 posture that becomes genuine, not merely theoretical, security debt once Phase 2 ships adapters that process adversarial input by design.

### If Option B/C (isolation) is adopted at Phase 2
The IPC and authentication pattern already specified in §12.3 and already used for the Qwen3-TTS worker gets its first "core-to-worker for a security reason" application, which should make it a well-trodden pattern by the time the elevated-action helper needs it too.

### Deferral cost
Rising sharply at the Phase 2 boundary. Before Phase 2, no adapter exists, so deferral costs nothing. Once Phase 2 ships adapters processing real untrusted content, every additional adapter built in-process is one more component that would need retrofitting into a process boundary later if B/C is eventually chosen — cheapest to decide before the first adapter's implementation pattern is set, not after several exist and a migration has to move them all at once.

## Related

PRD FR-150, FR-154, NFR-040, §11.4, ARCHITECTURE.md §2 driver 2, §4.1, §4.2, §8, §13 gap 2, ADR-0012 (shell technology), ADR-0019 (browser profile isolation — the adapter most exposed to this risk).
