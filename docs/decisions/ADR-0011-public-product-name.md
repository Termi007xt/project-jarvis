# ADR-0011: Public Product Name

- **Status:** Open — decision required before Phase 6
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.1, §1.16, §17.3
- **Decision required before:** Phase 6 (Productisation — installer branding, Store/website listing, marketing copy)

## Context

PRD §1.16 instructs the implementation agent to "treat 'Jarvis' as an internal codename until product naming and trademark review are complete." §17.3 requires an "original application name" among the assets obtained before public distribution, and explicitly forbids using "Marvel character artwork, film audio, actor voice likenesses, or other protected branding without legal clearance." "Jarvis" (and its stylised form "J.A.R.V.I.S.") is strongly associated with the Marvel/Iron Man franchise in popular culture. Even where the bare word is not a registered mark in every relevant class, a personal-AI-assistant product named "Jarvis" invites plausible confusion with that franchise, which is exactly the kind of risk §17.3 is written to avoid. `PROJECT_INPUTS.md` already records `public_product_name: undecided`, i.e. the project owner has deliberately left this open rather than defaulting to the codename.

The risk is asymmetric with development timing: internal use in source code, documentation, and this repository is low risk (a private codename is not a public offering). The risk crystallises specifically at public distribution — installer name, Store listing, marketing text, screenshots, any public repository name, support channels. Nothing in Phase 0–5 requires this to be resolved; it becomes load-bearing only when Phase 6 packaging and public-facing assets are produced.

## Options considered

### Option A — Rename before public release
Choose a distinct original public product name; keep "Jarvis" as an internal-only codename exactly as §1.16 already instructs. A user's *personal* assistant can still be named "Jarvis" through the personality profile's editable `Name` field (FR-043) without the *product* itself being marketed under that name.
**Pros:** lowest legal risk, no dependency on a legal-clearance timeline blocking release, clean trademark search for a genuinely new name, no conflict with §17.3's Marvel-artwork prohibition.
**Cons:** user-visible identity split — a tester who has been calling it "Jarvis" installs something with a different public name; all Phase 6 branding assets (icons, installer graphics, documentation screenshots) must use the new name; rebrand cost grows with how much user-facing text already hardcodes "Jarvis."

### Option B — Keep "Jarvis" internal-only from the start, treat the eventual public name as always-separate
Functionally the same outcome as Option A, but framed as a standing policy rather than a late pivot: since §17.3 already requires original branding assets regardless (icon set, installer graphics, sounds), the naming decision is folded into that greenfield branding work rather than treated as a rename-in-progress.
**Pros:** same legal benefits as A, avoids ever presenting "Jarvis" as the committed public name even provisionally, which reduces the chance that public-facing collateral (a public repo, a demo video) accidentally ships under the codename before the decision is finalised.
**Cons:** requires discipline during Phase 0–5 to avoid leaking the codename into anything that might become public before the rename is planned.

### Option C — Seek legal clearance for "Jarvis" as the public name
Commission a trademark clearance search (even an informal one — USPTO TESS plus a common-law search) and, if clear in the relevant classes and jurisdictions, register and use "Jarvis" or a stylised variant publicly.
**Pros:** preserves the identity already used throughout testing and documentation; avoids a rebrand.
**Cons:** real cost and time for a solo/indie project; PRD §1.16 already signals the project owner does not want progress gated on this; the downside of clearing incorrectly (a takedown or cease-and-desist after users have already installed under the name) is worse than simply not using it.

## Decision

Deferred. No option is selected yet, consistent with PRD §1.16's explicit deferral. Given the project's current scale (solo/indie, per `PROJECT_INPUTS.md`) and PRD §17.3's explicit prohibition on unlicensed Marvel-adjacent branding, the pragmatic lean is toward Option A/B (rename before public release), but this is not being formally decided here.

## Decision criteria

1. A candidate public name passes a basic US/EU trademark-availability screen (informal search acceptable) with no direct conflict in software / digital-assistant classes.
2. A matching domain name and package identifiers (installer AppId, MSIX Package Family Name if ADR-0022 selects MSIX, a public repository name if the project is ever made public) are available under the chosen name.
3. The chosen name is not confusingly similar to existing Microsoft Store listings in the same category.
4. If Option C is pursued instead, a documented legal opinion is obtained before any public asset ships bearing "Jarvis."
5. Internal codename usage in source code, config keys, and documentation may continue regardless of outcome — the rename is a display/branding-layer change, not a rewrite, provided user-facing strings are not hardcoded (see Consequences).

## Consequences

### If Option A/B (rename) is the eventual outcome
The cost of the rename is bounded by how disciplined Phase 0–5 are about not hardcoding "Jarvis" as a *user-facing* string. Keeping `project_codename` internal and introducing a distinct `public_product_name` configuration value wherever user-facing text is rendered (window titles, tray tooltip, installer name) means the eventual rename touches a small, enumerable set of places rather than the whole codebase.

### Deferral cost
Rising slowly but steadily. Every additional Phase 0–5 artefact that hardcodes "Jarvis" as user-facing text (rather than reading a config value) increases the future rename cost. The tray icon and window title already implemented per ARCHITECTURE.md §6.10 currently display "Jarvis" directly — inexpensive to change today, materially more expensive once installer graphics, a Store listing, and documentation screenshots exist (Phase 6). Deciding before Phase 6 asset production begins is the cheapest point to resolve this.

## Related

ADR-0022 (MSIX distribution — Package Family Name depends on the final name), ADR-0026 (code signing — certificate subject name is a legal-entity concern, largely decoupled from the product name), PRD §1.16, §17.3.
