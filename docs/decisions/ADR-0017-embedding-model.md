# ADR-0017: Embedding Model

- **Status:** Proposed — a tentative default is configured but not yet benchmarked
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.7, FR-041
- **Decision required before:** Phase 3 (memory retrieval first makes embeddings load-bearing), hardening further ahead of Phase 4 (file-content indexing)

## Context

FR-041 requires the system support separate models per role — conversation/planning, vision, embeddings, speech recognition, speech output — so no component hard-codes a single model. `config/defaults.yaml` currently configures `models.embeddings: { provider: ollama, name: qwen3-embedding:0.6b, context_length: 8192 }`, and `PROJECT_INPUTS.md` records the same. Unlike the TTS voice (ADR-0014) or screenshot retention (ADR-0025) defaults, which `PROJECT_INPUTS.md` marks as verified, the embedding model carries no such marker — it is a working default, not a benchmarked one.

The embedding model is used wherever the architecture derives vector representations from canonical text: memory retrieval (FR-163 — "only relevant memories shall be retrieved into a prompt" implies semantic search over stored memories), and, once Phase 4 lands, local document and file-content indexing. ARCHITECTURE.md §9 is explicit that "everything else — the embedding index, the file index, caches — is derived and rebuildable, and must never hold unique information" (PRD §14.1). This constraint lowers the stakes of the choice considerably: switching models later means recomputing the index, not migrating or losing data, because the index is required by design to be rebuildable from the canonical SQLite records.

The competing consideration is resource cost: the planner (`qwen3.5:9b-q4_K_M`) and vision (`qwen3-vl:8b-instruct-q4_K_M`) models already contend for the 12 GB VRAM budget on the RTX 5070 — exactly the concern behind FR-039's resource scheduler and `model_runtime.load_strategy: sequential`. An embedding model is typically small (`qwen3-embedding:0.6b` is roughly the same order of magnitude as the deferred Qwen3-TTS model at 0.6B parameters) but it is also the most *frequently invoked* of the three — plausibly every memory write and retrieval touches it, unlike the planner (per-turn) or vision (occasional) — so latency and co-residency behaviour with the planner matter more than raw size alone would suggest.

## Options considered

### Option A — Keep `qwen3-embedding:0.6b` (current tentative default)
**Pros:** already wired into `config/defaults.yaml` and the Ollama-based routing path (FR-041); same model family as the planner/vision choices, which may simplify tokenizer/quantization tooling and reduces the number of distinct model families to test and document; small enough to plausibly stay resident alongside the planner without triggering the sequential-unload path.
**Cons:** unverified — no recorded dimensionality, benchmark latency, or retrieval-quality measurement exists yet; the model's actual output dimensionality, which determines per-record storage cost in the derived index, has not been confirmed against DATA_MODEL.md's assumptions.

### Option B — A dedicated, retrieval-purpose-built embedding model (e.g. a BGE- or Nomic-family model)
**Pros:** purpose-built for embeddings rather than being a general chat-model family's embedding head; often has well-published, independently reproduced retrieval benchmarks that de-risk whether FR-163's retrieval actually works well; typically smaller and faster than a 0.6B general-purpose-family variant.
**Cons:** a different model family than the planner/vision choices — a separate download, separate licence check (§17.2), and one more entry in the model-compatibility test matrix (§15.4), without Option A's family-sharing convenience.

### Option C — No fixed default; the first-run wizard (§16) benchmarks on the user's hardware and recommends
**Pros:** most honest given the current "tentative, unverified" status — defers the choice to measured reality on the actual target machine rather than a documentation-time guess; extends the existing hardware-assessment and model-compatibility-test framework (§15.1–§15.4) to embeddings with modest effort.
**Cons:** more onboarding-wizard engineering before Phase 3 can rely on any concrete default; risks blocking Phase 3 memory work on wizard engineering that is more naturally a Phase 6 concern — a plain configured default (A or B) is cheaper for internal development even if the wizard eventually offers a choice.

## Decision

Deferred. No option is confirmed. `qwen3-embedding:0.6b` continues as the *working* development default (Option A, as already configured) so Phase 3 memory-retrieval work is not blocked, but it is not yet "Accepted" in the ADR sense — it has not been benchmarked, and its dimensionality and VRAM co-residency behaviour with the planner are unverified.

## Decision criteria

1. Measured retrieval quality (e.g. precision on a small hand-built "does this query retrieve the right stored memory" test set) for `qwen3-embedding:0.6b` versus at least one Option B alternative.
2. Confirmed output dimensionality, and the resulting per-record storage cost in the derived index at realistic memory/document-chunk volumes, checked against DATA_MODEL.md's schema assumptions.
3. Measured VRAM footprint when co-resident with `qwen3.5:9b-q4_K_M` (the common case, since both are plausibly loaded during a conversation that triggers memory retrieval), and whether this forces the sequential-load path FR-039 defines or can safely co-reside.
4. Embedding latency per call at conversational-turn frequency — this model is invoked far more often than the planner or vision model, so even small per-call latency compounds and must not dominate response time (§19.1 performance targets).
5. Cost of changing the model later, expressed concretely as "how long does a full reindex take at expected data volumes" — since PRD §14.1 already guarantees the index is rebuildable and holds no unique information, the question is reindex time, not feasibility.

## Consequences

### If Option A (`qwen3-embedding:0.6b`) is confirmed after benchmarking
No migration is needed — it is already the configured default, so confirming it simply upgrades this ADR's status to Accepted with recorded evidence. Qwen-family consistency with the planner/vision models simplifies documentation, licensing review, and the model-compatibility test suite (§15.4).

### Deferral cost
Moderate and rising with Phase progress: memory retrieval (FR-163) is a Phase 3 deliverable and file-content indexing is Phase 4, so an unbenchmarked embedding model risks being discovered inadequate only after real memory/document data has already been indexed under it. Because the index is rebuildable by design, a late model swap is not a data-loss event, but it is a re-indexing cost that grows with the volume already indexed — cheapest to resolve before Phase 3 substantially populates the index, not after.

## Related

ADR-0014 (a parallel "tentative-but-configured default" pattern for TTS), PRD §14.1, §15.1–§15.4, FR-041, FR-163, DATA_MODEL.md.
