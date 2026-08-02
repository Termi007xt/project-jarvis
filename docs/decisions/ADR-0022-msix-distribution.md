# ADR-0022: MSIX Distribution

- **Status:** Open — decision required before Phase 6
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.12, §18.1, §18.4
- **Decision required before:** Phase 6 (Productisation — determines the shape of ADR-0013's installer work)

## Context

§12.1 lists packaging as "PyInstaller one-directory build preferred... Windows installer using an appropriate installer technology... Optional later MSIX packaging" — the PRD already treats MSIX as a possible *later* addition rather than a Phase 6 certainty. §25.12 asks specifically "whether MSIX becomes the primary distribution format," meaning the real question is not "MSIX or not at all" but "MSIX-as-primary versus MSIX-as-optional-secondary (or never)." §18.1's installer requirements apply regardless of format: per-user install by default, startup configuration, uninstall entry, data preserved across updates, explicit data-deletion offer at uninstall, prerequisite detection, repair, offline installation support. §18.4 requires signed update packages, manual and optional-automatic update checks, release notes, rollback for failed updates, schema migrations, and compatibility checks for skills/packs — MSIX has its own opinions about update mechanisms (Store-integrated, or App Installer / sideload) that interact with §18.4's requirements differently than a classic installer would.

The tension this ADR must resolve is architectural, not cosmetic: MSIX packages run in a lightly containerised environment (filesystem/registry virtualization, and — if Store-distributed — an AppContainer-style sandbox with a declared capability list) designed to make apps easier to install, update, and uninstall cleanly, but that containerisation is in real tension with what this product structurally needs to do. FR-004's scoped-elevation helper, UI Automation driving arbitrary third-party windows (FR-070/FR-071, the entire Automation Worker), global hotkeys (FR-018, emergency stop in §11.3), startup registration (FR-002), and a per-user data vault the user can relocate outside the package's own storage area (§14.2, NFR-025) are all things classic Win32 desktop apps do easily, and packaged/sandboxed apps have historically had a harder time with — some are outright restricted under full Store sandboxing, others require the sparse-package/unpackaged-with-MSIX-installer hybrid model or specific, sometimes review-gated capability declarations.

## Options considered

### Option A — MSIX becomes the primary distribution format
Package the product as MSIX (Store-distributed or sideloaded via App Installer), embracing its update model and per-user install semantics as the primary path; ADR-0013's classic installer becomes secondary/offline-only or is dropped.
**Pros:** clean uninstall (MSIX's virtualization guarantees near-total removal, directly helping §18.1's uninstall requirements); built-in update infrastructure if Store-distributed (helping §18.4's signed-package and rollback aspects "for free"); modern Windows integration story; per-user install is MSIX's default posture, aligning naturally with FR-003.
**Cons:** UI Automation driving other applications, global hotkey registration, and broad filesystem access for a user-relocatable vault are exactly the capabilities hardest to reconcile with MSIX's sandboxing without falling back to restricted capabilities that may need Store justification, or without using the unpackaged-plus-MSIX-installer hybrid (which somewhat defeats the sandboxing benefit that motivated choosing MSIX); Store certification, if pursued, would review an app whose entire purpose is automating other applications and reading screen/window content — a category that historically draws extra scrutiny.

### Option B — MSIX as a secondary/optional channel, classic installer remains primary
Ship the primary public build through a classic installer (ADR-0013), and separately offer an MSIX package for users who specifically want Store-style install/uninstall cleanliness, accepting that the MSIX variant may need to run unpackaged with restricted capabilities or ship reduced functionality.
**Pros:** the primary distribution path is unconstrained by sandboxing limits, so FR-004, UI Automation, global hotkeys, and vault relocation all work exactly as designed without capability negotiation; MSIX remains available as a genuine convenience for users who prefer it, without gating the whole product's architecture on satisfying its constraints.
**Cons:** maintaining two packaging pipelines is real ongoing cost for a small project; the MSIX variant may end up meaningfully feature-limited compared to the classic-installer build, risking user confusion about behavioural differences.

### Option C — No MSIX; classic installer only
Do not pursue MSIX for the foreseeable future.
**Pros:** lowest cost; avoids the sandboxing-versus-automation tension entirely; keeps all engineering effort on one packaging path.
**Cons:** forgoes Store discoverability and the cleanest-possible uninstall/update story MSIX offers; §25.12 explicitly poses this as an open decision to resolve, so choosing "never" should be a deliberate, criteria-based conclusion rather than a default by inaction.

## Decision

Deferred. No option is selected yet. Given the concrete conflict between MSIX's sandboxing model and this product's core mechanism (broad UI Automation, global hotkeys, and a relocatable vault), Option B (classic installer primary, MSIX optional-secondary if pursued at all) is the lower-risk starting lean, to be confirmed against real capability-declaration testing rather than assumed.

## Decision criteria

1. A prototype MSIX package is tested against the actual Phase 2+ feature set (UI Automation on arbitrary third-party windows, global hotkey registration, startup registration, vault relocation outside `%LOCALAPPDATA%`) to determine which capabilities work unmodified, which need explicit capability declarations, and which do not work at all.
2. If Store distribution is in scope, Microsoft Store policy is checked for automation/accessibility-tooling apps specifically (this product's category), for any category-specific restrictions beyond generic MSIX capability declarations.
3. §18.4's rollback-for-failed-updates requirement is verified achievable in whichever channel(s) are chosen — MSIX's own update model handles some of this natively if Store-distributed, but a sideloaded MSIX via App Installer needs the same rollback discipline as a classic installer.
4. The per-user vault (§14.2) and its relocation feature are proven to work correctly under MSIX's storage virtualization, including relocation to a path outside the package's own virtualized storage area.
5. Engineering cost of maintaining two packaging pipelines (if Option B) is weighed honestly against the marginal benefit of Store presence, given the project's current single-owner scale.

## Consequences

### If Option B (classic primary, MSIX optional) is chosen
ADR-0013 can proceed largely independent of this ADR's outcome, since the primary installer's technology choice does not need to satisfy MSIX's constraints. An MSIX variant, if built later, is additive scope that can be revisited without blocking Phase 6 exit criteria, which require "a signed installer," not specifically MSIX.

### Deferral cost
Moderate. This ADR should close before ADR-0013 is finalised, since "is MSIX primary" materially changes what ADR-0013 needs to decide (a classic installer built assuming it is secondary can be simpler than one built as the sole public distribution path with full offline-install support). Leaving both ADRs open simultaneously risks circular blocking; resolving this one first, even provisionally in Option B's direction, unblocks ADR-0013.

## Related

ADR-0013 (installer technology), ADR-0012 (shell technology — a native shell narrows the MSIX capability gap somewhat for the shell surface, though not for the automation worker), §18.1, §18.4, §14.2, FR-003, FR-004, FR-018, FR-070/FR-071.
