# ADR-0015: Additional TTS Providers

- **Status:** Accepted (provider set, interface, and isolation architecture); scheduling-arbitration policy remains open
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.5, FR-035–FR-039
- **Decision required before:** Phase 4 (vision fallback and long-running workflows, where GPU contention between vision and expressive TTS first becomes concrete); the provider-neutral interface itself is needed from Phase 1

## Context

FR-035 requires a provider-neutral TTS interface with provider-specific code kept out of conversation/task logic, and fixes the initial provider priority: Kokoro as the default local voice provider, Windows SAPI as the emergency fallback, Qwen3-TTS as an optional experimental expressive provider. FR-036 forbids silently changing voice providers or speaker identities mid-conversation — a switch requires explicit user selection, a settings change, or a documented fallback caused by provider failure, and any fallback must be displayed as a temporary unavailability, not hidden. FR-037 scopes "expressive" (emotion instructions, speaking style, pacing, emphasis, streaming, selectable speaker profiles) and requires it stay disabled by default until it passes local performance, consistency, licensing, and resource tests. FR-038 requires the Qwen3-TTS integration specifically to run in an isolated Python 3.12 worker: a separate process, typed authenticated local IPC, explicit health checks, bounded startup time, clean shutdown, and no direct access to Jarvis tools or permissions. FR-039 requires GPU-backed TTS to participate in a model resource scheduler that prevents unsafe simultaneous loading of the planner model, vision model, GPU-backed TTS, and other high-memory GPU workloads, via unloading, sequential loading, VRAM checks, provider fallback, and visible degradation status.

`config/defaults.yaml` and `PROJECT_INPUTS.md` already encode this concretely: `kokoro_bm_george` (CPU, `enabled: true`), `windows_sapi` (`enabled: true`, `fallback_only: true`), and `qwen3_tts_expressive` (`Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`, Python 3.12, `execution_mode: isolated_worker`, CUDA, `enabled: false`, `status: experimental`), with an explicit activation policy: never switch voice silently, user selects the active voice profile, benchmark before product activation. ARCHITECTURE.md §6.9's model-role separation and §12.3's authenticated-IPC requirement for any process split are the mechanisms this already assumes; §8's extension-point table lists `TtsProvider.speak(text, style) -> audio` with exactly these three consumers. This is therefore largely settled architecture. What remains genuinely open is *when and under what measured conditions* Qwen3-TTS graduates from `enabled: false`/`experimental`, and exactly how the resource scheduler arbitrates it against the planner and vision models on the 12 GB RTX 5070.

## Options considered

### Option A — Strict mutual exclusion
The scheduler treats GPU-backed TTS as mutually exclusive with the vision model: Qwen3-TTS may load only while the vision model is unloaded, matching the currently configured `model_runtime.load_strategy: sequential` and `allow_parallel_heavy_models: false`.
**Pros:** simplest to reason about and test; avoids VRAM exhaustion outright; consistent with the sequential-loading stub ARCHITECTURE.md §13 gap 6 already flags as "configuration only" pending enforcement.
**Cons:** a task wanting both vision and expressive speech in close succession pays a reload-latency penalty each time.

### Option B — VRAM-budget-aware co-residency
The scheduler estimates each model's VRAM footprint and allows co-residency when the sum plus a safety margin fits in 12 GB, falling back to Option A's exclusion only when it does not.
**Pros:** better latency when the budget allows it — Qwen3-TTS's 0.6B footprint is small relative to the 8–9B planner/vision models, so co-residency is often genuinely safe.
**Cons:** requires real VRAM measurement (KV-cache growth with context length matters, not just parameter-count arithmetic), more failure modes to test, contradicts the simpler default already shipped.

### Option C — Never enable Qwen3-TTS by default; explicit per-session opt-in only
Regardless of scheduler sophistication, keep `enabled_by_default: false` indefinitely, requiring a manual toggle rather than opportunistic auto-activation.
**Pros:** lowest-surprise default; matches FR-037's "disabled until tested" and FR-036's "never switch silently"; avoids the scheduler ever having to interrupt an active expressive-voice session to free VRAM for a vision task.
**Cons:** does not by itself resolve how the scheduler arbitrates once the user has opted in — Option A or B is still needed underneath.

## Decision

**Accepted** for the provider set, interface, and isolation model (Kokoro default / SAPI fallback / Qwen3-TTS deferred, experimental, isolated), exactly as configured today. **Open** for the specific scheduling-arbitration policy between Option A and B. Option C (opt-in only, never auto-enabled) is accepted as a standing constraint regardless of which of A/B governs the scheduler internals, since it is already encoded in `config/defaults.yaml` and directly required by FR-037.

## Decision criteria

1. Measured VRAM footprint of `qwen3.5:9b-q4_K_M` + `qwen3-vl:8b-instruct-q4_K_M` + `Qwen3-TTS-12Hz-0.6B` loaded together on the RTX 5070 12 GB, at Phase 4 vision-workflow context lengths.
2. Whether the measured co-residency case leaves enough headroom for KV-cache growth during a long conversation without an out-of-memory failure.
3. Reload latency under Option A's exclusion strategy stays within the "concise progress update" tolerance of FR-033, so switching does not itself become a user-visible stall.
4. FR-039's required capabilities (unloading, sequential loading, VRAM checks, provider fallback, visible degradation status) are all implemented and tested before Qwen3-TTS activation is offered, regardless of which arbitration policy is chosen.

## Consequences

### If Option A (strict exclusion) is retained
Lower implementation risk, ships sooner, matches the currently configured sequential-load strategy exactly — no scheduler rework beyond what ARCHITECTURE.md §13 gap 6 already tracks. The cost is paid in reload latency whenever vision and expressive speech are wanted close together, which Phase 4's "rich progress updates" deliverable should surface honestly rather than hide.

### Deferral cost
Low. The provider and isolation architecture are already fixed and Qwen3-TTS ships `enabled: false`, so nothing blocks Phase 1–3 delivery. The scheduling-policy decision only needs to close before Phase 4, when vision and expressive TTS first coexist; leaving it open past that point risks the scheduler being retrofitted under time pressure instead of designed deliberately.

## Related

ADR-0014 (default English voice), ARCHITECTURE.md §4.2 (process-separation trigger table names the Qwen3-TTS worker), §6.8, §6.9, §8, §13 gap 6, PRD §12.3.
