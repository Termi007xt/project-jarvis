# ADR-0021: Encrypted Sync and Backup

- **Status:** Open — decision required before Phase 6
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.11, FR-168–FR-170
- **Decision required before:** Phase 6 (Productisation); does not block Phase 0–5

## Context

FR-168 lists what a user may export as part of their "portable identity": personality, preferences, memories, application aliases, skills, permissions template, model selections, voice selections, task templates, prompt templates, and optionally conversation history. FR-169 requires API keys, cookies, tokens, and credentials be excluded from *normal* exports. FR-170 allows a separate, optional, explicitly warned, passphrase-protected encrypted export that may include secrets. ARCHITECTURE.md §9 and PRD §14.2 already show `backups/` and `exports/` as vault subdirectories — *local* backup/export is already part of the baseline data architecture. This ADR is specifically about whether anything leaves the machine at all, a materially different question given PRD §4.1's "local first, not local only" principle, PROJECT_INPUTS.md's `default_network_mode: local_assistant`, and the telemetry-off default (§18.5).

Sync/backup that leaves the device is qualitatively different from local export because it turns a single compromise point (this machine) into two (this machine and wherever the backup lives), and because "cloud storage" implies an ongoing relationship with a third party the product does not otherwise require. The PRD's local-first stance makes "no sync, local-only backup" a philosophically consistent default; the open question is whether to build *optional* cloud backup as a convenience feature for users who want cross-machine continuity or disaster recovery beyond "keep a copy of the vault folder yourself."

## Options considered

### Option A — No sync; local backup only
Build only what §14.2's `backups/` directory already implies: a local backup/restore mechanism (a scheduled or manual snapshot of `jarvis.db` plus attachments into `backups/`, or an on-demand `.jarvispack`-style export the user can copy anywhere themselves), with zero built-in network transport.
**Pros:** simplest to build and reason about; zero new secret-handling surface, since nothing is ever transmitted (FR-169/FR-170's export-secret rules remain the only relevant safeguard); fully consistent with §4.1 and the telemetry-off default; no dependency on a third party's availability, pricing, or API changes.
**Cons:** cross-machine continuity is entirely the user's manual responsibility; no protection against local disaster (drive failure) unless the user separately backs up the backup.

### Option B — User-supplied cloud storage with client-side encryption
Let the user point Jarvis at storage they already control (e.g. a folder that happens to sync via OneDrive/Dropbox/Google Drive, or an explicit S3-compatible endpoint with user-supplied credentials), encrypting the backup client-side before it touches that storage, so the third party only ever sees ciphertext.
**Pros:** meaningfully more convenient for continuity; keeps the product free of any backend to operate, since the product never touches a shared server — only the user's own already-existing cloud account; naturally extends FR-170's existing encrypted-export-with-passphrase concept from a one-off action into an ongoing sync.
**Cons:** real engineering cost (key derivation/management, conflict handling if sync happens from two machines, versioning so a schema migration on one machine does not produce an unreadable backup for another) disproportionate without clear demand; "user-supplied cloud storage" still needs a defined integration point (a generic folder? specific provider SDKs?) with its own scope-creep risk; sync introduces new steady-state failure modes (partial upload, encryption-key loss meaning a permanently unrecoverable backup) that must be handled honestly (§4.6).

### Option C — None; backup is entirely the user's own responsibility
Provide only the relocatable, exportable vault already required by §14.2/NFR-025, with no dedicated "backup" feature beyond what export/import (FR-168) already provides.
**Pros:** avoids building a feature that duplicates what any user can already do by copying a folder or using their own backup tool against the vault path; keeps scope minimal, consistent with §26's ruthless-scope guidance.
**Cons:** under-serves less technical users unlikely to think to manually back up an AppData folder; does not distinguish itself from "just don't build this feature," which may not match expectations set by FR-168's fairly complete export list.

## Decision

Deferred. No option is selected yet. Option A (local backup only, no network transport) is the safe, low-cost default consistent with everything already fixed (§4.1, telemetry-off default, no-shared-secrets posture in §18.3), and is likely sufficient unless real user demand for cross-machine continuity emerges.

## Decision criteria

1. FR-169's secret-exclusion rule is verifiably enforced for any backup/sync path chosen — a test should assert that a default local backup, and any future cloud-sync payload, exclude API keys, cookies, tokens, and credentials by default, with secrets included only via the explicit FR-170 passphrase-protected path.
2. If Option B is pursued, the encryption scheme (algorithm, key derivation, where the key/passphrase is held — ideally never leaving the local Windows-protected credential store per NFR-022) is specified and reviewed before any cloud-transport code is written.
3. If Option B is pursued, the simplest version that still satisfies "user-supplied storage, client-side encrypted" (e.g. a local folder path the user points at their own sync client) is preferred over a feature-complete multi-provider integration.
4. Restore is tested, not just backup — including the cross-machine case (restoring onto a fresh install) and the schema-version case (restoring a backup made by an older schema version, per NFR-043's migration requirement).
5. Whichever option is chosen, it does not silently change `default_network_mode` — sync must remain something the user explicitly enables, never a default-on behaviour.

## Consequences

### If Option A (local-only) remains the answer
Phase 6 ships a straightforward local backup/restore feature building directly on the `backups/` directory PRD §14.2 already anticipates and the export/import baseline Phase 3 already delivers; no new secret-in-transit surface is ever created — the simplest possible position to defend in a security review (§19.3).

### Deferral cost
Low. Nothing in Phase 0–5 requires sync; local export/import (FR-168, Phase 3 baseline) already gives users a portable copy of their identity. The cost of leaving this open is mostly opportunity cost rather than a blocking dependency — it can be added post-1.0 without disrupting the local-first architecture, since Option B's design does not require any change to how the vault is structured today.

## Related

PRD §4.1, §14.2, §14.6, §18.3, §18.5, NFR-022, NFR-025, ADR-0020 (parallel reasoning about avoiding a project-operated backend service).
