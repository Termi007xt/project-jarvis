# ADR-0006: Layered Configuration with Override-Only Persistence

- **Status:** Accepted
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §12.1, §14.2, NFR-041
- **Phase:** 0

## Context

Project Jarvis ships defaults for a large configuration surface — model
routing, audio device selection, privacy posture, storage location — and
every one of those defaults must be user-overridable without the user ever
hand-editing a schema-fragile file. Two requirements collide here in a way
that is easy to get wrong: the product must ship improved defaults over time
without a config-file update silently discarding a user's customisation, and
it must also make a typo in a settings file loud rather than quietly
ignored. A naive "one big settings file the user edits directly" design gets
neither property: shipping a new default either has to overwrite the user's
whole file (destroying their changes) or never touch it again (meaning the
user's copy of every untouched default silently goes stale).

The vault itself also needs a single, well-defined location that can be
relocated by the user (PRD §14.2: "User may relocate the data vault from the
GUI"), and every test needs an isolated filesystem location so the test
suite never touches a developer's real `%LOCALAPPDATA%`.

## Options considered

### Option A — Three layers merged deepest-first, override-only persistence (chosen)
**Pros:** `config/defaults.yaml` (shipped, read-only, version-controlled) is
always the full picture; `user.yaml` (in
`%LOCALAPPDATA%\ProjectJarvis\config\`) holds only the delta from defaults;
`JARVIS_*` environment variables sit on top for development and test
overrides. A pydantic model with `extra="forbid"` validates the merged
result into one frozen tree.
**Cons:** Requires a deep-merge implementation and a corresponding
deep-diff-against-defaults implementation for saving, rather than a flat
read/write of a single file — more code than "just persist whatever the
user has".

### Option B — Single flat settings file, whole-file persistence
**Pros:** Simplest possible implementation; what the user sees on disk is
exactly what is in effect.
**Cons:** Shipping a new default either clobbers the user's edits on next
save or requires migrating the user's file forward on every release, and a
typo in a key the user never meant to touch degrades silently unless the
loader is unusually strict. This is the exact failure mode Option A is built
to avoid.

### Option C — Registry-based configuration (Windows Registry)
**Pros:** Native Windows mechanism, some built-in ACL and per-user scoping.
**Cons:** Not human-readable or diffable, harder to include in an export
package (PRD §14.6), awkward to make portable across machines or to unit
test without touching a real registry hive, and outside the spirit of a
local-first, fully user-owned, fully exportable product. Rejected.

## Decision

Configuration is resolved in three layers, merged deepest-first, then
validated into one frozen pydantic model tree:

```
config/defaults.yaml                                  (shipped, read-only)
   ↓ deep merge
%LOCALAPPDATA%\ProjectJarvis\config\user.yaml          (user overrides only)
   ↓ deep merge
JARVIS_* environment variables                         (dev/test overrides)
   ↓ validate
AppConfig  (pydantic, extra="forbid", schema_version pinned)
```

Key decisions within this, each justified independently:

- **Only the difference from defaults is persisted** in `user.yaml`. Shipping
  a new default therefore changes behaviour for every setting the user has
  not touched, and never silently reverts a setting the user has explicitly
  chosen — the two properties Option B could not deliver simultaneously.
- **`extra="forbid"` everywhere in the validated model.** A typo in a
  settings key becomes a precise startup error naming the offending path,
  not a value that is silently dropped and never takes effect.
- **Writes are atomic.** Settings are written to a temporary file in the same
  directory and then renamed into place, so a crash mid-save cannot leave
  `user.yaml` half-written and unparseable on the next launch.
- **Windows environment-variable expansion happens in exactly one place**:
  `jarvis.config.paths.VaultPaths`. `%LOCALAPPDATA%` and `%USERPROFILE%` are
  expanded there and nowhere else in the codebase.
- **`JARVIS_DATA_DIR` relocates the entire vault.** This single environment
  variable both implements the user-facing relocation requirement (PRD
  §14.2) and gives every automated test an isolated vault, so no test run
  ever touches a real user's `%LOCALAPPDATA%`.
- Changing a setting at runtime publishes `ConfigChanged` on the event bus
  (ADR-0005), so components react to the new value rather than needing to
  re-read configuration defensively on every use.

## Enforcement

- The pydantic model's `extra="forbid"` is itself the enforcement mechanism
  for the "typo is loud" property — there is no separate check to
  circumvent.
- Path resolution is enforced by convention plus code review: any new
  `%VARNAME%`-style expansion introduced outside `VaultPaths` is a review
  finding, since it would create a second, inconsistent place where vault
  location logic could diverge.
- Atomic write (temp file + rename in the same directory) is exercised by
  tests that simulate an interrupted save and assert `user.yaml` remains
  parseable.
- Config-merge behaviour (defaults + overrides + env, in that precedence
  order) is covered by unit tests (ARCHITECTURE.md §11,
  `tests/unit/` — "config merge" is named explicitly in the testing table).
- Every test obtains an isolated vault through `JARVIS_DATA_DIR`
  (ARCHITECTURE.md §11), which is both a testing convenience and a
  continuous exercise of the relocation code path itself.

## Consequences

### Positive
- Default improvements ship safely: a user who never touched
  `audio.speech_to_text.model` gets the new default automatically; a user
  who explicitly chose a different model keeps their choice, forever, until
  they change it again.
- Configuration errors are startup-time and precise, not runtime and
  mysterious — a strong fit for NFR-041's typed-schema requirement.
- The vault-relocation mechanism and the test-isolation mechanism are the
  same code path, which means relocation is exercised constantly in CI
  rather than being a rarely-tested GUI feature.

### Negative
- A deep merge plus a deep diff-against-defaults is more code, and more
  subtle code (list-merge semantics in particular need a documented rule),
  than a flat read/write.
- Because only the delta is persisted, inspecting `user.yaml` alone does not
  show the effective configuration — a user or developer must look at the
  merged, validated result (e.g. via a GUI settings view or a diagnostic
  dump) to see what is actually in effect.

### Residual risk
This does not solve configuration drift between the shipped
`config/defaults.yaml` and documentation or the PRD itself — nothing
currently guarantees the two stay in sync beyond review discipline. It also
does not solve the case where a user's `user.yaml` was hand-edited outside
the app in a way that happens to still validate but expresses an unintended
combination of settings (e.g. an override that made sense under an older
default that has since changed underneath it); `extra="forbid"` catches
unknown keys, not semantically stale ones.

## Revisit when
- The configuration surface grows large enough that a GUI-only settings
  experience (no direct `user.yaml` editing expected) changes what "loud
  failure on typo" needs to mean for end users, as opposed to developers.
- A second, non-Windows target platform is ever considered, at which point
  `VaultPaths`' Windows-specific expansion logic needs a real abstraction
  rather than a single well-known location.

## Related
- ADR-0002 (SQLite as source of truth — configuration itself is the one
  piece of durable state deliberately kept outside SQLite, as files, so it
  can be relocated and edited independently of the database).
- ADR-0005 (event bus — `ConfigChanged` propagation).
- ARCHITECTURE.md §6.1 (configuration system), §11 (testing architecture).
- PRD §14.2 (default data location and relocation).
