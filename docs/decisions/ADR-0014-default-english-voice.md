# ADR-0014: Default English Voice

- **Status:** Accepted (development default); redistribution licensing for a public build remains open
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.4, FR-030, FR-031, FR-032
- **Decision required before:** Phase 6 (public redistribution licensing must be confirmed before a build reaches a non-developer user; Phase 1 proceeds today under the accepted default)

## Context

FR-030 requires local TTS by default. FR-031 requires the GUI to support installed voice packs with preview, rate, pitch (where supported), volume, and language controls. FR-032 requires every *redistributable* voice pack to carry licence metadata, and requires user-imported voices to stay outside the installer unless redistribution is explicitly authorised. `PROJECT_INPUTS.md` and `config/defaults.yaml` already record a concrete, verified selection: Kokoro (`hexgrad/Kokoro-82M`) running on CPU under Python 3.11, British English (`language_code: "b"`), voice `bm_george`, speed `1.0`, status `selected_and_verified`, configured as `text_to_speech.active_profile: kokoro_bm_george`, with Windows SAPI configured as the `fallback_only` provider. This matches ARCHITECTURE.md §8's extension-point table (`TtsProvider` with "Kokoro, SAPI fallback, Qwen3-TTS worker" as consumers).

This ADR records an already-made decision rather than opening a new one. What is genuinely unresolved is narrower than "which voice": Kokoro-82M's weights are distributed under a permissive licence from `hexgrad` on Hugging Face, which is favourable for redistribution, but the *specific voice pack file* (`bm_george`) and the bundled pronunciation dictionary (`espeak-ng`, which carries GPL-family licensing considerations of its own) need their licence terms re-verified at the point the installer would bundle or auto-download them for end users other than the developer. PRD §17.3 explicitly lists "default voice with redistribution rights" as an asset to obtain before public distribution, and §17.2 requires every runtime download to show provider, licence, approximate size, install location, and whether it can be redistributed.

## Options considered

### Option A — Kokoro `bm_george` as default, Windows SAPI as fallback (accepted)
Local, CPU-only (no VRAM contention with the planner/vision models on the shared 12 GB RTX 5070 budget), British English, already verified working end-to-end.
**Pros:** zero VRAM cost, no runtime network dependency, already integration-tested, SAPI fallback requires no extra download since it ships with Windows.
**Cons:** Kokoro's expressiveness is limited compared to larger neural TTS (which is why Qwen3-TTS exists as a deferred expressive option, ADR-0015); British English as the sole default may not match every future user's expectation.

### Option B — Piper as the baseline (as PRD §12.1/§15.2 originally suggested)
§12.1 and §15.2 both name Piper as "the stable local baseline," predating the Kokoro verification recorded in `PROJECT_INPUTS.md`.
**Pros:** Piper voices carry well-understood, clearly redistributable per-voice licences already familiar in the open-source TTS community, which would have simplified the §17.3 redistribution question.
**Cons:** superseded in practice — `PROJECT_INPUTS.md` and `config/defaults.yaml` have already moved past this and verified Kokoro instead; reverting would discard working, tested configuration for no functional gain.

### Option C — Windows SAPI as the primary default, not just fallback
**Pros:** zero licensing risk (OS-provided), zero download size.
**Cons:** noticeably lower voice quality than Kokoro; contradicts the "local, high-quality default" product intent; `PROJECT_INPUTS.md` already designates SAPI as fallback-only, so promoting it would be a regression from a verified working decision.

## Decision

**Accepted.** Kokoro `bm_george` (British English, CPU, `hexgrad/Kokoro-82M`, Python 3.11) is the default TTS voice for development and Phase 1 delivery, exactly as configured in `config/defaults.yaml` and `PROJECT_INPUTS.md`. Windows SAPI remains the configured emergency fallback. The open sub-decision, tracked here, is whether `bm_george`'s licence and `espeak-ng`'s pronunciation-dictionary licence permit bundling or auto-download for third-party end users at Phase 6, or whether the public build must instead prompt for a first-run download from the original source under its own licence terms.

## Decision criteria

1. Kokoro-82M and the `bm_george` voice weights' licence text is re-read at the exact commit/release the installer would pin, confirming redistribution — not merely local use — is permitted.
2. `espeak-ng`'s licence (GPL-family) is checked against the distribution model chosen in ADR-0013/ADR-0022, since GPL obligations differ between "installer downloads espeak-ng from its own installer at first run" and "installer bundles espeak-ng binaries directly."
3. §17.2's per-download disclosure (provider, licence, size, redistribution status) is implemented in the first-run wizard regardless of the bundling answer, since even a first-run download needs this UI.
4. If licensing blocks bundling, a documented first-run download path from the canonical source is proven compatible with §18.1's offline-installation requirement, or is explicitly scoped out of the offline path.

## Consequences

### If the accepted default (Kokoro `bm_george`) continues unchanged through Phase 6
No runtime rework is needed — this ADR closes the "which voice" question outright. Packaging work (ADR-0013) only needs to answer "download at first run" versus "bundle in installer," not re-evaluate the voice itself. British-English-only as the sole shipped default is a separate product-scope question that may warrant its own future ADR if multi-accent defaults become a goal.

### Deferral cost
Low for the runtime decision, already closed. The redistribution-licensing sub-question has a hard deadline: it must close before any Phase 6 installer build ships to a user who is not the developer, since §17.3 lists "default voice with redistribution rights" as a precondition for public distribution, and §18.1's offline-installation requirement cannot be fully tested until the bundling question is answered.

## Related

ADR-0015 (additional TTS providers — Qwen3-TTS, SAPI), PRD §17.2, §17.3, §18.1, FR-030–FR-032.
