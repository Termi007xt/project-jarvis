# ADR-0008: Secret Storage Deferred to Phase 1

- **Status:** Accepted (deferral); mechanism Open
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §18.3, NFR-022, FR-169, FR-170
- **Phase:** 0

## Context

Project Jarvis will eventually hold user-supplied secrets: a search provider
key, an optional cloud model key, an optional TTS provider key, optional
integration tokens (PRD §18.3). The PRD is explicit about what these must
satisfy once they exist: they must be stored using Windows-protected
credential storage, never in plaintext configuration files (PRD §18.3,
NFR-022); they must be excluded from normal exports (FR-169); and an
optional, explicitly warned, passphrase-protected encrypted export may
include them separately (FR-170).

Phase 0, by design, has no computer-control capability whatsoever
(ARCHITECTURE.md §12) and no external integration that requires a credential
of any kind — there is no search provider call, no cloud model call, no
integration token to protect, because none of those features exist yet. This
ADR exists to record, deliberately, that building a secret store now would
be speculative infrastructure with no consumer to validate it against, and to
capture the reasoning and the candidate mechanisms so that decision is not
rebuilt from scratch when Phase 1 actually needs it.

## Options considered

These are the candidate mechanisms for *when* a secret store is built, not a
choice being made now — recorded here so Phase 1 starts from an evaluated
position rather than a blank page.

### Option A — DPAPI (`CryptProtectData`/`CryptUnprotectData`) via `ctypes`
**Pros:** Windows Data Protection API ties encryption to the logged-in
user's credentials with no separate key-management story required from the
application; no third-party dependency; works for arbitrary blobs, so it
composes naturally with "encrypt a value, store the ciphertext in SQLite or
a file"; matches NFR-022's "Windows-protected secret storage" literally.
**Cons:** `ctypes` bindings to a Win32 API are unforgiving to get wrong
(buffer lifetime, `DATA_BLOB` marshalling) and need careful testing; DPAPI
keys are tied to the Windows user profile, so secrets do not survive a
profile reset or migrate cleanly to a new machine without an explicit
re-entry step — which is arguably the correct behaviour for this product,
but must be a deliberate choice, not a surprise.

### Option B — Windows Credential Manager (`CredWrite`/`CredRead`)
**Pros:** A purpose-built OS facility for exactly this (named credentials,
per-user scoped, visible and manageable through the standard Windows
Credential Manager UI, which gives users an OS-native way to inspect what is
stored); no need to design a storage schema for secrets at all.
**Cons:** Designed around a flat namespace of named credentials rather than
structured per-integration metadata; entry count and payload size have
practical OS-imposed limits; slightly less control over the storage format
than a self-managed encrypted table, which matters if secrets ever need
associated metadata (expiry, scope, last-used) beyond what Credential
Manager's schema offers.

### Option C — An encrypted SQLite table with a DPAPI-wrapped key
**Pros:** Keeps secrets inside the same canonical store as everything else
(consistent with ADR-0002's "SQLite is the single source of truth" for
transactional state, provided the *unencrypted* secret itself never becomes
part of a query-able column); DPAPI protects only the table's symmetric key,
not every value individually, which is cheaper if there end up being many
secrets; naturally supports the metadata (per-secret scope, creation time,
last-used) a flat OS credential store does not.
**Cons:** More code to build and to security-review than either OS-native
option — a home-grown envelope-encryption scheme is exactly the kind of
thing that is easy to get subtly wrong (nonce reuse, key rotation, secure
erasure of the decrypted value from memory); duplicates protection Windows
already offers natively via Options A or B, for a marginal metadata benefit
that could also be achieved by keeping the metadata unencrypted alongside a
DPAPI- or Credential-Manager-protected value.

No option is selected in this ADR. The comparison above is the input to that
decision when Phase 1 needs to make it.

## Decision

**No secret store is implemented in Phase 0.** Phase 0 handles no secrets —
there is no search provider integration, no cloud model integration, no
token-bearing integration of any kind — so building a secret store now would
be code with no consumer, validated against nothing, and liable to be wrong
in ways that would only surface once a real secret needed protecting.

The constraint the eventual implementation must satisfy is fixed now, even
though the mechanism is not:

- Secrets are stored using Windows-protected storage, never in plaintext
  configuration (PRD §18.3, NFR-022) — this rules out ever adding a
  `secrets:` block to `user.yaml` (ADR-0006), even temporarily or for
  development convenience.
- Secrets are excluded from normal exports (FR-169) — the export pipeline
  must positively identify and skip secret-bearing entities, not merely
  happen not to include a table that does not exist yet.
- An optional, separate, passphrase-protected encrypted export may include
  secrets, only after an explicit warning (FR-170).

## Enforcement

- There is no secret-store code to misuse in Phase 0, which is itself the
  strongest enforcement available: the absence of the capability means the
  absence of the risk.
- `config/defaults.yaml` and the `AppConfig` schema (ADR-0006) contain no
  secret-shaped fields in Phase 0; `extra="forbid"` would in any case reject
  an ad-hoc secret field added to `user.yaml` outside the schema, giving an
  early, loud signal if someone tries to smuggle a credential through the
  configuration layer instead of waiting for the real secret store.
- When the secret store lands, its design must be captured in a follow-up
  ADR that names the chosen mechanism from the options above (or a new one)
  and is reviewed before any tool depends on it.
- Redaction (`jarvis.core.audit.redaction`, ARCHITECTURE.md §6.3) already
  treats keys matching `api_key`, `token`, `secret`, `password`,
  `credential` and similar as sensitive and value-pattern-matches
  high-entropy strings and PEM blocks — so even before a dedicated secret
  store exists, an accidental secret making it into a tool parameter or log
  line is redacted before serialisation, as a defence-in-depth backstop, not
  as a substitute for real secret storage.

## Consequences

### Positive
- No speculative, unvalidated security-critical code sits in the codebase
  waiting for its first real use — the store will be designed against an
  actual consumer (the Phase 1 search API key) rather than a guess.
- The constraint is fixed and public now, so Phase 1 cannot quietly ship a
  "just put it in `user.yaml` for now" shortcut under time pressure; this
  ADR is the record that such a shortcut was considered and rejected before
  it could be proposed as an expedient.

### Negative
- Phase 1 has a hard dependency on this design-and-build work landing before
  its first secret-bearing feature (the optional search API key) can ship;
  it is not free-riding on Phase 0 work the way most Phase 1 features are
  free-riding on the permission engine and audit log already existing.

### Residual risk
This decision does not solve the problem for Phase 0 users who might
manually place a credential somewhere Jarvis reads today with the mistaken
belief that it is protected — there is no user-facing secret feature in
Phase 0 to create that expectation, but the risk becomes live the instant
Phase 1 ships a settings field asking for a key, and the chosen mechanism
must be genuinely in place before that field is exposed, not merely planned.

## Revisit when
The first secret comes into existence: the optional, user-supplied search
provider API key planned for Phase 1 (PRD §18.3). At that point this ADR's
"mechanism Open" status must be resolved by a follow-up ADR selecting one of
the options above (or a documented alternative), before the search
integration is allowed to store anything.

## Related
- ADR-0006 (layered configuration — the explicit reason secrets cannot live
  in `user.yaml`).
- ARCHITECTURE.md §6.3 (audit redaction, the interim defence-in-depth
  backstop), §8 (extension points — `SecretStore.get/set/delete` is listed
  as a defined-but-unimplemented Phase 1 extension point).
- PRD §18.3 (secrets and APIs), §18.5 (privacy and telemetry — the same
  "excluded from export by default" pattern applied to a different category
  of sensitive data).
