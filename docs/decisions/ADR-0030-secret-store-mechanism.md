# ADR-0030: Secret store mechanism — DPAPI with unencrypted metadata

- **Status:** Accepted (decided 2026-08-02)
- **Date:** 2026-08-02
- **Deciders:** Project owner
- **PRD reference:** §18.3, NFR-022, FR-169, FR-170, AT-016
- **Phase:** 1

## Context

ADR-0008 deferred the secret store out of Phase 0 with status **"mechanism
Open"**, evaluated three candidate mechanisms, and required a follow-up ADR
naming the chosen one *before any tool depends on it*. This is that follow-up.

Phase 1 is where the deferral expires. Nothing in Phase 1 strictly needs a
credential yet — Ollama is unauthenticated on loopback by design (ADR-0007), and
Kokoro, faster-whisper and openWakeWord are all local — but PRD §18.3 puts the
optional search provider key in Phase 1's neighbourhood, the Integrations screen
must stop claiming a capability that has no storage behind it, and ADR-0008's own
"Residual risk" section names the exact failure this ADR prevents: a settings
field that asks for a key before the protection behind it exists.

The constraints were already fixed by ADR-0008 and are not reopened here:
Windows-protected storage, never plaintext configuration; excluded from normal
exports; included in a passphrase-protected export only after an explicit warning.

## Decision

**Option A — DPAPI (`CryptProtectData` / `CryptUnprotectData`) via `ctypes`, with
per-secret metadata stored unencrypted alongside the ciphertext in SQLite.**

- The **value** is encrypted with DPAPI at `CRYPTPROTECT_UI_FORBIDDEN`, scoped to
  the current Windows user, and only the ciphertext is persisted.
- An additional **entropy** value derived per secret name is passed to DPAPI, so
  that ciphertext lifted out of the database cannot be unprotected by another
  process running as the same user without also knowing the name.
- The **metadata** — name, purpose, creation time, last-used time, which
  integration owns it — is stored unencrypted in a `secret` table, because it is
  not itself sensitive and because ADR-0008 identified the inability to hold this
  metadata as the specific weakness of Option B.
- `SecretStore` exposes exactly `get` / `set` / `delete` / `list_names`, matching
  the extension point already declared in ARCHITECTURE.md §8. It has **no**
  "list all values" or "export all" method: there is no API shape that returns
  every plaintext secret at once.
- The decrypted value is returned as a `str` to the immediate caller and is never
  cached, never logged, never placed on the event bus, never written to a
  checkpoint or task evidence, and never passed to the model.

This is Option A, not Option C: DPAPI protects each value directly rather than
protecting a home-grown symmetric key over a home-grown envelope scheme. ADR-0008
was right that Option C's marginal metadata benefit is available without its
cost — keeping the metadata unencrypted next to a DPAPI-protected value is
precisely how that benefit is obtained, and it is what this ADR does.

Option B (Credential Manager) is rejected on ADR-0008's own analysis: a flat
named-credential namespace with no room for per-secret scope and last-used
metadata, and payload limits that constrain a design that has no reason to be
constrained.

### On Linux

DPAPI is Windows-only. `SecretStore` reports itself **unavailable** on any other
platform rather than silently falling back to a weaker scheme or to plaintext.
A feature needing a secret is then shown disabled and honest (ADR-0010), exactly
as an unbuilt feature is. The engine must still import and test on Linux (CI
enforces this), so the unavailability is a runtime state, never an import error.

## Options considered

Restated from ADR-0008 §Options, which did the comparison work: **A — DPAPI via
ctypes** *(chosen)*; **B — Windows Credential Manager**; **C — encrypted SQLite
table with a DPAPI-wrapped key**. No new option emerged. The change since ADR-0008
is only that a decision is now required, and that the metadata requirement — which
was the one thing pulling toward Option C — is satisfiable under Option A.

## Enforcement

- `tests/security/test_secret_store.py`: a stored secret's plaintext appears
  nowhere in `user.yaml`, nowhere in `jarvis.db`, and nowhere in `audit.jsonl`,
  verified by scanning the actual bytes of each after a round trip.
- A stored secret is absent from a normal export (FR-169, AT-016).
- `AppConfig` still rejects any secret-shaped key, so the ADR-0006 route stays
  closed; `extra="forbid"` gives the loud early signal ADR-0008 relied on.
- `SecretStore` has no method returning more than one plaintext value — asserted
  against the class surface, so the shape cannot drift.
- On a non-Windows platform, `SecretStore.available` is `False` and `set` raises
  rather than storing anything.
- The `ctypes` DPAPI binding is exercised on Windows against a real round trip,
  including a tampered-ciphertext case that must fail closed rather than return
  partial data.

## Consequences

### Positive
NFR-022 is satisfied literally, with no key management of Jarvis's own invention
and no third-party dependency. Per-secret metadata is available for the
Permissions and Integrations screens, so a user can see what is stored, what uses
it and when it was last used, and delete it. ADR-0008's deferral closes cleanly
rather than lapsing.

### Negative
`ctypes` marshalling of `DATA_BLOB` is unforgiving — buffer lifetime and
`LocalFree` handling have to be right, and getting them wrong is the kind of
defect that shows up as an intermittent crash rather than a test failure. The
binding is small but is genuinely security-critical code, and it is Windows-only,
so the Linux CI leg proves only that it is absent, not that it is correct.

### Residual risk
DPAPI protects against another *user* on the machine and against theft of the
database file. It does not protect against malicious code already running as this
user — such code can call `CryptUnprotectData` too. That is the correct threat
boundary for a single-user local agent (SECURITY.md §1.3 disclaims replacing OS
security), but it must not be described to users as protection against local
malware. Secrets also do not survive a Windows profile reset and do not migrate to
a new machine; ADR-0008 judged this correct behaviour, and it means export and
re-entry is the supported migration path, not a copied file.

## Revisit when
A secret needs to be readable by a helper process running under a different
identity (the ADR-0009 elevation helper is the plausible candidate), or a secret
must survive machine migration without re-entry — either would break the DPAPI
user-scoping assumption and reopen Options B and C.

## Related
ADR-0008 (the deferral this resolves — its "Revisit when" pointed here),
ADR-0006 (layered configuration — why secrets can never live in `user.yaml`),
ADR-0007 (Ollama is unauthenticated on loopback, so it needs no secret),
ADR-0010 (honest degraded UI — unavailable on Linux is shown, not hidden),
ARCHITECTURE.md §8 (`SecretStore.get/set/delete` extension point),
SECURITY.md §14 (status table row moves from Deferred to Implemented only once
the tests above pass), PRD §18.3, NFR-022, FR-169, FR-170, AT-016.
