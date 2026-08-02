# ADR-0012: Shell Technology for the First Public Build

- **Status:** Open — decision required before Phase 6
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.2, §10.4 ("Architecture Decision: Version 1 implementation language"), §12.1, §12.2
- **Decision required before:** Phase 6 (Productisation — packaging and public distribution)

## Context

ADR-0001 already commits Phase 0 through Phase 3 to a single Python 3.11 + PySide6 process, and fixes that Rust/Tauri "may later replace the native application shell, but only after Phase 3 and only if performance or distribution measurements justify it." PRD §10.4 (the "Architecture Decision: Version 1 implementation language" block) is more specific about scope: a future native shell might replace the system tray, startup integration, global hotkeys, updates, secure IPC, and selected Windows-native utilities, while AI inference, speech, browser automation, and high-level orchestration may remain Python sidecars. It requires the decision be based on *measured* startup latency, idle memory, packaging reliability, crash isolation, update requirements, and Windows integration limitations — and states plainly: "Rust shall not be adopted solely for theoretical performance."

This ADR does not reopen that timing question — it is settled that Rust/native cannot be introduced before Phase 3 measurements exist. What PRD §25.2 asks, narrower and separable, is which shell technology the *first public build* actually ships with once Phase 6 packaging begins: continue the Python-only PySide6 shell (extended and hardened), or move to a native .NET/Rust/Tauri shell with the existing Python components demoted to sidecar processes over the typed local IPC that PRD §12.3 and ARCHITECTURE.md §4.2 already require for any process split. The reference hardware (RTX 5070 12 GB, Ryzen 9 7900X, 32 GB RAM) is not the constraint here — the drivers are packaging quality, always-on idle footprint for a tray-resident application, and Windows integration surfaces (global hotkeys, notification actions, startup registration) that are more naturally exposed by a native shell.

## Options considered

### Option A — Python-only shell (status quo, extended)
Continue PySide6 for the public build; harden PyInstaller packaging (one-directory build per §12.1) and add native Windows integration via pywin32/ctypes as needed.
**Pros:** zero migration cost, single codebase and process model already validated through Phase 0's exit criteria, fastest path to Phase 6, does not require anything ADR-0001 currently forbids.
**Cons:** Python interpreter/DLL startup overhead is real for an always-resident tray app; PyInstaller onedir builds carry a larger footprint and slower cold start than a native exe; idle memory for a process hosting Qt plus in-thread workers is higher than a slim native shell; crash isolation is weaker — a defect in an in-process worker can still destabilise the shell, the same structural gap ARCHITECTURE.md §13 gap 2 names for adapters (see ADR-0023).

### Option B — Native .NET (WinUI 3 / WPF) shell with Python sidecars
Rewrite the shell (tray, main window, approval dialogs, global hotkeys, startup registration, notifications, updater) in .NET; `jarvis.core`, `jarvis.tasks`, `jarvis.llm`, `jarvis.audio`, `jarvis.automation` remain Python, running as sidecar processes over authenticated local IPC (§12.3).
**Pros:** best Windows integration (hotkeys, notification action buttons, Store/MSIX alignment), lower idle memory and faster cold start for the resident shell, structural crash isolation (a Python sidecar crash cannot take the tray down), pairs naturally with MSIX packaging (ADR-0022) where a small native front-end is easier to certify than a PyInstaller bundle.
**Cons:** two languages and toolchains; every domain event ARCHITECTURE.md §5–6 defines must cross a real process boundary with schema validation and authentication instead of the in-process EventBus; the approval dialog (§11.2) and audit-visible state must stay synchronised across that boundary with no silent drift; a meaningful rewrite before Phase 6 ships, with schedule risk.

### Option C — Rust/Tauri shell with Python sidecars
As ADR-0001 names as the eventual candidate, using Tauri instead of .NET.
**Pros:** smaller binary and lower memory than .NET; keeps the technology named in ADR-0001; preserves cross-platform optionality (not a current goal, but a side benefit).
**Cons:** the same IPC-boundary rewrite cost as Option B, without .NET's more mature ecosystem for UIA integration, notification action buttons, and Store submission tooling; a smaller pool of Rust+Tauri+Windows-automation expertise to draw on.

## Decision

Deferred. No option is selected yet, as required by ADR-0001's measurement-driven gate. The Phase 0–3 Python-only path (Option A) continues to be built by default; ADR-0001 forbids introducing Rust before Phase 3 measurements exist, and this ADR does not contradict that.

## Decision criteria

1. Cold-start time from process launch to interactive tray icon, Option A versus a native-shell prototype, against a defined regression threshold (e.g. native must beat Python by a clear margin to justify rewrite cost).
2. Idle RSS memory after a sustained period with wake detection running, compared across shell technologies.
3. Clean-machine install-and-first-run success rate across a matrix of Windows 11 builds (missing VC++ runtime, AV false positives, DLL search-path issues) — if Option A does not clear a defined reliability bar, Option B/C is preferred regardless of other metrics.
4. Whether crash isolation actually matters in observed practice by Phase 4/5 — has the automation worker (ARCHITECTURE.md §13 gap 2) produced in-process crashes that a process boundary would have contained?
5. Global-hotkey registration reliability and notification action-button support achieved in Python versus a native shell.
6. An honest engineering-cost estimate for the IPC-boundary rewrite (Option B/C) against the remaining Phase 4–6 timeline.

## Consequences

### If Option A (Python-only) remains the choice through Phase 6
The public build ships as a hardened PyInstaller onedir package; ADR-0013 (installer) and ADR-0022 (MSIX) must be evaluated against Python-packaging realities (larger payload, runtime-dependency detection) rather than a slim native exe. Crash isolation stays a known gap into the public release, which increases the importance of ADR-0023 (adapter isolation) as a partial mitigation.

### Deferral cost
Low through Phase 0–5, provided the existing discipline holds: ARCHITECTURE.md §4.1 already requires `jarvis.core`, `jarvis.tasks`, `jarvis.storage`, `jarvis.llm`, and `jarvis.config` never import PySide6, and §6.2's EventBridge is the only place domain events cross into Qt. That discipline is exactly what keeps this decision cheap to defer — every feature built directly against PySide6 signals rather than through the typed EventBridge increases the eventual IPC-boundary rewrite cost if Option B/C is chosen later.

## Related

ADR-0001 (Rust deferred), ADR-0013 (installer technology), ADR-0022 (MSIX distribution), ADR-0023 (adapter isolation — the crash-isolation argument overlaps), ARCHITECTURE.md §2 driver 6, §4, §13 gap 2.
