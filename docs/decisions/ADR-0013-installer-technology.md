# ADR-0013: Installer Technology

- **Status:** Open — decision required before Phase 6
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.3, §18.1
- **Decision required before:** Phase 6 (Productisation — "signed installer" is an explicit exit criterion)

## Context

PRD §18.1 fixes firm requirements regardless of which technology builds the installer: per-user install by default (consistent with FR-003's non-administrator default), startup configuration offered, an uninstall entry created, user data preserved across updates, explicit data-deletion offered at uninstall, prerequisite detection, repair support, and optional offline installation with bundled and licensed dependencies. NFR-024 additionally requires the installer and update packages be signed. §12.1 names only "an appropriate installer technology" without selecting one, and separately flags "Optional later MSIX packaging" — MSIX is covered by its own decision (ADR-0022) because it is a packaging *format* with Store-certification implications, not merely an installer *builder*. This ADR covers the classic installer technology used if MSIX is not the primary format, or used alongside it for a non-Store channel.

Whichever technology is chosen must respect the vault layout ARCHITECTURE.md §6.1 and PRD §14.2 define (`%LOCALAPPDATA%\ProjectJarvis\`, itself user-relocatable): the installer must not silently delete `user.yaml` overrides or the SQLite vault on an in-place update. "Preserves user data during updates" is a correctness requirement, not a nice-to-have — ARCHITECTURE.md §6.1's config-layering design ("only overrides are persisted") exists specifically so that upgrading changes behaviour only for untouched settings and never reverts a user's choice; an installer that does not honour this at the file-system level would undermine that design.

## Options considered

### Option A — Inno Setup
Free, Pascal-like scripting, mature, widely used for per-user Windows installs.
**Pros:** straightforward per-user install mode; easy conditional logic for prerequisite detection (Ollama presence, VC++ runtime, GPU driver); well-documented patterns for data preservation across updates and explicit uninstall-time deletion; small learning curve; large community precedent for exactly this "install an app, download large assets post-install" shape (matching §16's onboarding-driven model downloads).
**Cons:** not a native Windows Installer database — no Group Policy / enterprise deployment story (largely irrelevant for a personal desktop agent, but worth naming); code signing is a manual `signtool` step wired into the build rather than integrated tooling; repair is scripted rather than a first-class MSI feature.

### Option B — WiX Toolset (MSI)
Produces a real Windows Installer (.msi) package.
**Pros:** native repair/modify/uninstall semantics from the OS itself; well-understood upgrade-code-based versioning model that maps cleanly onto "preserve user data across updates"; mature enterprise tooling if ever needed.
**Cons:** steeper authoring curve (verbose XML); per-user MSI has known rough edges — MSI tooling and defaults historically lean per-machine, requiring deliberate configuration (`MSIINSTALLPERUSER`) to avoid unwanted elevation prompts; heavier toolchain than this project's current scale needs.

### Option C — NSIS
Free, script-based, minimal runtime footprint, long history in the open-source Windows-installer space.
**Pros:** very small installer binary; flexible custom scripting for exactly the logic this product needs (model downloads are explicitly a first-run wizard concern per §16, not an installer concern, which reduces how much custom installer logic is actually required).
**Cons:** more idiosyncratic scripting language than Inno's; smaller ecosystem of maintained examples for the specific "preserve data, offer deletion at uninstall" pattern; less commonly recommended in current Microsoft guidance than MSI/MSIX.

### Option D — MSIX (boundary note only)
Fully covered by ADR-0022; noted here only to draw the scope line: if ADR-0022 selects MSIX as primary, this ADR's remaining scope narrows to whether a classic installer is still offered as a secondary/offline channel, since §18.1's offline-installation requirement (bundled, licensed dependencies) is easier to satisfy outside the Store's sandboxing model.

## Decision

Deferred. No option is selected yet. The requirements in §18.1 are satisfiable by any of A/B/C; the deciding factor is downstream of ADR-0022 (MSIX as primary or not) and, secondarily, ADR-0012 (shell technology), so resolving those first materially narrows this choice.

## Decision criteria

1. Whether ADR-0022 selects MSIX as the primary distribution format — if yes, this ADR only needs to cover a secondary/offline installer, favouring the simpler Option A or C.
2. Verified per-user install with no UAC elevation prompt at any step, tested on a clean non-administrator Windows 11 account (this validates FR-003's non-administrator default at the install layer, not just at runtime).
3. A working "preserve on update, offer deletion on uninstall" flow demonstrated against the real vault layout, including the relocated-vault case (§14.2 permits relocation; the installer must not assume the default path).
4. Prerequisite detection correctly identifies a missing VC++ runtime and reports (rather than silently installs) a missing Ollama, consistent with §16's onboarding wizard owning the Ollama connect/install flow.
5. Repair re-establishes a broken install (missing or corrupted binaries) without touching `jarvis.db` or `user.yaml`.
6. Code-signing integration (`signtool` or equivalent) is wired into the build pipeline before Phase 6 exit, per NFR-024.

## Consequences

### If Option A (Inno Setup) is chosen
Fastest path to a working signed installer, given strong community precedent for this exact "install, then download large assets" shape. The main engineering cost shifts to writing careful pre-install/post-install/uninstall scripts that respect the vault layout — in particular, the "offer explicit data deletion" prompt at uninstall must be an opt-in dialog, never a default action, to avoid an accidental destructive default.

### Deferral cost
Low near-term — Phase 0–5 do not need an installer; developers run from source. The cost concentrates at the Phase 6 boundary: if ADR-0022 is still open when Phase 6 begins, this ADR cannot close either, and the "signed installer" exit criterion blocks. Resolving ADR-0022 first is the cheapest sequencing.

## Related

ADR-0012 (shell technology), ADR-0022 (MSIX distribution), ADR-0026 (code signing and updates), PRD §18.1, §14.2, FR-003.
