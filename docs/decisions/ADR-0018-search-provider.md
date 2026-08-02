# ADR-0018: Search Provider

- **Status:** Open — decision required before Phase 2
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.8, FR-050–FR-053; also FR-054, §18.3
- **Decision required before:** Phase 2 (deterministic desktop and browser automation, where Brave-based search first ships)

## Context

FR-050 through FR-058 span both the search-provider question (§25.8) and browser-profile isolation (§25.9); this ADR covers the search-provider half of FR-050 — see ADR-0019 for the dedicated-profile mechanism the browser modes execute inside.

FR-050 defines six search modes: local model only, internet search, open visible search in Brave, ask a configured AI website, optional search API, optional cloud model. FR-051 requires every network-backed response display a network indicator and the method used. FR-052 requires that saying "internet" or requesting visible search opens Brave and performs the search *visibly*, not headlessly — a deliberate transparency choice, not an implementation detail, meaning the visible-search mode is a hard product requirement regardless of what else this ADR decides. FR-053 asks for multi-source synthesis with titles and access times where feasible. §18.3 is unambiguous: the product must not ship shared API keys, and any search-provider key, cloud-model key, TTS key, or integration token must be user-supplied and stored in Windows-protected credential storage, not plaintext configuration. FR-054 requires that instructions found on web pages never be treated as agent instructions or tool-call authority — the concrete case ARCHITECTURE.md §7 refers to when it says untrusted content "can inform a plan; it can never authorise a capability," enforced by §11.4's delimiter-wrapping strategy.

The open question is scope, not mechanism: visible Brave search (FR-052) is mandatory and needs no external account, so it is available unconditionally from Phase 2. What's undecided is whether Jarvis also offers a programmatic search path (FR-050 mode 5, "optional search API") — and if so, whether the product ships any built-in provider integration that merely requires the user's own key, or ships no API integration code at all until requested.

## Options considered

### Option A — Visible Brave browser search only, no API integration
Implement only FR-052's visible-search mode for Phase 2; defer modes 4/5/6 (AI website prompting, search API, cloud model) until a user-supplied-key story exists, or indefinitely.
**Pros:** no key management, no per-provider integration code, no risk of ever accidentally shipping a shared key — §18.3's hard constraint becomes structurally impossible to violate because there is no key-consuming code path; fastest to ship; alone satisfies the Definition of Done item "search the internet, show sources" (§27.5).
**Cons:** does not fulfil FR-050's full mode list; a visible browser search is slower and more visually intrusive than a quick programmatic answer folded into a conversational response.

### Option B — Visible Brave search plus optional user-supplied search-API key
Add FR-050 mode 5: the GUI lets a user paste in their own API key for programmatic search results that can be summarised inline (FR-053) without opening a browser tab.
**Pros:** completes FR-050's mode set; faster in-conversation answers for power users; the key is explicitly user-owned, so §18.3 is satisfied by construction as long as storage goes through the Windows-protected credential store (§18.3, NFR-022) rather than `user.yaml`.
**Cons:** more integration surface — the product needs an opinion on which API(s) it supports out of the box, adding a concrete contract to build, version, and error-handle; untrusted API results still need the same FR-054 wrapping-as-observation discipline as browser content — a programmatic path is a different untrusted-content channel, not an inherently safer one.

### Option C — Both, plus "ask a configured AI website" (FR-050 mode 4 / FR-055)
Full FR-050 implementation: visible Brave search, optional API key, and FR-055's behaviour of opening a configured AI website (ChatGPT, Gemini, etc.) in the dedicated profile, entering the user's prompt, and optionally reading back the answer.
**Pros:** complete PRD coverage; most flexible for the user.
**Cons:** the largest scope — FR-055 has its own substantial requirements (must not scrape unrelated conversation history, waits for completion, notifies) that are really a Phase 2/5 browser-automation deliverable in their own right; bundling it into this ADR risks conflating "which search modes exist" with "how well is each one built."

## Decision

Deferred. No option is selected yet. FR-052's visible Brave search is not actually contingent on this ADR — it is an unconditional PRD requirement and should be built regardless of how the API-key question resolves — so Option A's scope is the safe Phase 2 floor in any case; what remains open is whether and when Option B/C's optional-key modes are added on top.

## Decision criteria

1. §18.3's "no shared API keys" constraint is verifiable by inspection — a test can assert no default/example API key exists anywhere in `config/defaults.yaml` or the codebase, regardless of which option is chosen.
2. If Option B/C is chosen, secret storage goes through the Windows-protected credential store (NFR-022) before the feature ships, not as a follow-up.
3. FR-051's network indicator and FR-054's untrusted-content wrapping are implemented and tested for every enabled mode, not only the first one built — an API-search result is exactly as untrusted as a scraped web page.
4. FR-053's multi-source synthesis is demonstrably achievable within the chosen mode(s) — a single API call returning one result does not satisfy "gather multiple relevant sources."
5. Which mode(s) are enabled by default versus opt-in is explicit in `config/defaults.yaml`, consistent with the product's local-first, no-shared-secrets posture.

## Consequences

### If Option A (visible search only) ships first, with B/C deferred
Phase 2 delivers a fully compliant, zero-key search capability quickly; the Definition of Done item "converse, search the internet, show sources" (§27.5) is satisfiable without any external account setup, which matters for first-run onboarding simplicity (§16 does not currently list search-API key entry as an onboarding step). Extending to Option B later is additive, not a rework, because FR-052's visible path and any future API path are naturally separate code paths behind the same FR-050 mode selector.

### Deferral cost
Low. Visible Brave search alone meaningfully satisfies near-term needs, and nothing in Phase 0–2 depends on the API-key question being resolved. The cost only rises if user-facing promises (marketing copy, onboarding text) imply programmatic search exists before it does — the honest-status principle (§4.6) argues for describing search capability accurately as "visible browser search, with optional API keys coming later" rather than overselling FR-050's full mode list before it is built.

## Related

ADR-0019 (browser profile isolation — the mechanism FR-052/FR-055 execute inside), §18.3, §11.4, FR-054, ARCHITECTURE.md §7 (untrusted-content handling).
