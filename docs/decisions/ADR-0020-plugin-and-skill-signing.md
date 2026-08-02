# ADR-0020: Plugin and Skill Signing

- **Status:** Open — decision required before Phase 6
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.10, FR-105, FR-110, §14.5
- **Decision required before:** Phase 6 (Productisation — "Plugin/adapter SDK" deliverable, and any public skill-pack sharing)

## Context

§14.5's skill manifest schema already includes a `signed: false` field as a first-class, always-present element of every skill — alongside `id, name, version, description, aliases, risk_level, enabled, required_permissions, required_apps, variables, resource_locks, entrypoint, created_by`. That the field exists and defaults to `false` while no signing mechanism exists yet is itself informative: the schema was designed anticipating this ADR's outcome without presupposing it. FR-105 requires no newly recorded or AI-generated skill become active without explicit user approval — the baseline safety net that already exists regardless of signing. FR-110 requires skills be exportable independently or inside a `.jarvispack` (§14.6). `created_by` distinguishes `user | recorder | import | developer` — imported skills are already a distinct, tracked provenance category, separate from ones the user recorded on their own machine.

The attack surface this ADR addresses is specifically the *imported* skill pack — §14.6 defines `.jarvispack` as a ZIP-compatible archive that can contain a `skills/` directory, and §17.4 already requires imported skill packs to display licence and source fields, implying the product always anticipated skills flowing between users. A skill is not inert data: per §14.5 it declares `required_permissions`, `required_apps`, and `resource_locks`, and its `workflow.json` entrypoint encodes a sequence of UI Automation elements, browser selectors, and keyboard/mouse actions (FR-101) that will *execute* through the same ToolInvoker pipeline (ARCHITECTURE.md §6.6) as any other agent-proposed action. A malicious or merely careless imported pack is therefore a realistic path for a user to be talked into approving something harmful, which then requests broad `required_permissions` — the permission engine (§6.4) and FR-105's approval gate are the actual safety boundary, but signing determines how much a user can trust a pack's *stated* metadata (author identity, unmodified-since-publication) before they even reach that approval screen.

## Options considered

### Option A — No signing; mandatory user approval is the only gate
Build no signing infrastructure. Rely entirely on FR-105 (explicit approval before any skill activates) and the permission engine's per-capability evaluation (§6.4) to bound what an imported skill can do, regardless of authorship.
**Pros:** zero infrastructure cost (no key management, signing authority, or revocation story); arguably sufficient in principle, since if the approval dialog (§11.2, showing exact scope and risk category) is trustworthy, authorship is secondary to what is actually permitted at execution time; keeps `signed: false` simply true for everything, which is honest rather than a half-built feature.
**Cons:** does nothing to help a user judge, *before* approval, whether a pack is what it claims to be — the dialog can show "requests clipboard read/write and browser automation" but not "unmodified since the author published it" or "really is from the claimed author"; relies entirely on the user reading and understanding a possibly-long permission list correctly every time, exactly the approval-fatigue risk signing schemes exist to mitigate.

### Option B — Self-signed developer keys (no central authority)
Let skill authors generate their own signing key and sign `.jarvispack` exports; Jarvis verifies the signature matches the bundled public key and displays a stable author identity (fingerprint) across imports, so a user can at least tell "this is the same author as last time" and detect in-transit tampering, without any central registry vouching for who the author is.
**Pros:** cheap relative to Option C (no server, no review process); meaningfully raises the bar over Option A by detecting tampering; consistent with the project's local-first, no-central-dependency posture (no server this small/solo project would need to operate).
**Cons:** does not prevent a bad actor from generating a fresh key and signing something malicious — it proves internal consistency, not trustworthiness; the GUI must communicate this limited guarantee accurately, since a naive "Signed ✓" badge would overstate what self-signing proves.

### Option C — Project-operated signing authority
Stand up a signing service that reviews and signs skill packs before they carry a "verified" mark, analogous to a lightweight app-store review process.
**Pros:** the strongest guarantee among the three — a "signed" pack has actually been reviewed by someone accountable, closest to what users likely assume "signed" means.
**Cons:** substantial ongoing operational cost (someone reviews submissions indefinitely), disproportionate for a project currently scoped as single-owner, local-first (§4.1, `PROJECT_INPUTS.md`) with no stated marketplace plan; introduces a dependency on project-owner availability that contradicts the local-first, no-required-backend philosophy elsewhere in the PRD.

## Decision

Deferred. No option is selected yet. Given the project's current scope (single developer, local-first, no stated marketplace), Option A is the pragmatic near-term floor — FR-105's approval gate already exists and is the real safety boundary — with Option B as the natural next step if skill packs start moving between people who are not the developer.

## Decision criteria

1. Whether the product actually develops a distribution channel for skills between *different* users — if not, Option A may remain sufficient indefinitely, since there is no meaningful "who signed this" question when the only author is the installer's own publisher.
2. If skills are shared, the approval dialog (§11.2) is confirmed to already surface enough information (`required_permissions`, `required_apps`, `resource_locks`, `risk_level`) for an informed decision even without a trust mark — signing should raise the floor, not substitute for this disclosure.
3. For Option B: a key-generation and verification flow is prototyped and shown not to meaningfully burden a casual skill author.
4. For Option C: an honest estimate of ongoing reviewer time per submission exists, weighed against the project's actual (not aspirational) userbase size before committing.
5. `signed` remains a visible, honest field in the GUI regardless of outcome — a pack with `signed: false` must never be displayed ambiguously alongside a `signed: true` one without a clear explanation of what the field does and does not guarantee.

## Consequences

### If Option A (no signing, approval-only) remains the answer
Phase 3's skill editor and Phase 6's plugin/adapter SDK ship without signing-infrastructure cost; all safety continues to rest on FR-105's approval gate and the permission engine, which is already required regardless of this ADR. The `signed: false` field in every manifest is simply always accurate, consistent with the "no fake implementations" principle (§1.10).

### Deferral cost
Low through Phase 3 (self-recorded skills, single-user scenario, no import-from-a-stranger use case yet). Rises specifically when the product starts encouraging skill sharing between users — building trust infrastructure retroactively, after packs are already circulating under an unsigned convention, is harder than establishing it before sharing becomes common, since early adopters would need to be told their existing packs are now second-class.

## Related

PRD §14.5, §14.6, §17.4, FR-100–FR-110, §11.1, §11.2, ARCHITECTURE.md §6.4, §6.6.
