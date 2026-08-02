# ADR-0026: Code-signing and update infrastructure

- **Status:** Open — decision required before Phase 6 (first public build)
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.16, §18.1, §18.4, NFR-023, NFR-024, NFR-043, FR-224
- **Decision required before:** Phase 6 (Productisation)

## Context

Project Jarvis is an application that asks for permission to operate the user's
computer. That makes provenance a functional requirement, not a formality: a user
has no way to distinguish a genuine build from a tampered one except by
signature, and an unsigned agent asking to automate a desktop is exactly what a
cautious user should refuse.

Windows makes this concrete. An unsigned installer triggers a SmartScreen
"unrecognised app" warning that most users read as "this is malware". Signing
with a standard OV certificate removes the *unknown publisher* wording but not
the reputation warning, which clears only after enough installs accumulate. An EV
certificate grants SmartScreen reputation immediately but requires a hardware
token or a cloud HSM and costs several times more.

The update path carries the same weight. PRD §18.4 requires manual and optional
automatic update checks, signed update packages, release notes, rollback for
failed updates, schema migrations and compatibility checks for skills and packs.
An update mechanism that can install code is, by construction, the highest-value
target in the product: compromising it compromises every installation at once.

Two constraints are already fixed. The product must not ship shared API keys or
any shared secret (§18.3), so nothing in the release pipeline may embed
credentials in the artefact. Builds must include dependency and licence scanning
(NFR-023) — CI runs `pip-audit` and `pip-licenses` today, advisory only.

Nothing is signed at present, and there is no update mechanism. The About screen
states plainly that update checking is a Phase 6 capability and is not
implemented.

## Options considered

### Option A — OV code-signing certificate, manual update checks only

A standard organisation-validation certificate signs the installer and update
packages. The application checks a signed manifest when the user asks.

**Pros:** Lowest cost and least infrastructure. No always-on update service to
secure. A manual-only check means the update path cannot be triggered remotely,
which removes a whole class of attack. Adequate for a first public build with a
small user base.
**Cons:** SmartScreen reputation must be earned, so early users still see a
warning. Users on a stale version stay stale, including through a security fix.

### Option B — EV certificate, signed manifest, optional automatic checks

An extended-validation certificate on a hardware token or cloud HSM, with an
opt-in automatic check against a signed update manifest.

**Pros:** Immediate SmartScreen reputation — no warning from the first install.
Security fixes actually reach users. Matches what PRD §18.4 describes.
**Cons:** Materially more expensive and requires HSM-based signing in CI, which
is real infrastructure work. An automatic update path must be secured properly:
signature verification before execution, rollback on failure, and no silent
downgrade.

### Option C — MSIX through the Microsoft Store

Store distribution handles signing and updates as part of the platform.

**Pros:** No certificate to buy or manage. Updates and rollback are the
platform's problem. Store presence is a trust signal in itself.
**Cons:** MSIX packaging restrictions collide with what this product needs — UI
Automation against arbitrary applications, global hotkeys, startup registration,
a user-relocatable data vault. Store certification for an application whose
purpose is automating other applications is an open question. This is the subject
of its own decision (ADR-0022) and cannot be settled here.

## Decision

**Deferred. No option is selected yet.**

Option A is the leading candidate for the first public build, with a documented
migration path to Option B once there is a user base worth updating
automatically. That ordering keeps the expensive, security-sensitive
infrastructure until there is something to protect, without painting the project
into a corner: the artefact format and the manifest schema will be designed so
that adding automatic checks later does not change the update package format.

## Decision criteria

1. **Signature verification precedes execution, always.** An update package whose
   signature does not verify is discarded, not "warned about". This is testable
   with a deliberately corrupted package.
2. **No secret ships in the artefact.** The signing key never enters the build
   output; CI signs from a secret store or an HSM (§18.3).
3. **Rollback works and is tested.** A failed update restores the previous
   version and its data intact (§18.4). This includes a schema migration that
   half-applied.
4. **Schema compatibility is checked before an update installs**, not after. A
   database newer than the incoming binary is already a hard startup failure
   (ADR-0002, NFR-043); the updater must not create that situation.
5. **Skill and pack compatibility is checked**, and an incompatible skill is
   disabled with an explanation rather than silently failing at run time.
6. **The user can decline updates entirely** and remain on a working version.
7. **Dependency and licence scanning becomes blocking, not advisory**, before the
   first public build (NFR-023).
8. **Downgrade is not silent.** An update that would move the user to an older
   version requires explicit confirmation.
9. Measured before choosing between A and B: actual SmartScreen behaviour for an
   OV-signed installer from this publisher, and the real cost of HSM signing in CI.

## Consequences

### If Option A is chosen

**Positive:** The first public build ships without standing up update
infrastructure. The attack surface stays small: no automatic code delivery path
exists to compromise. Cost is proportionate to a product with few users.

**Negative:** Early users see a SmartScreen reputation warning, which for a
desktop automation agent is precisely the audience most likely to abandon the
install. Security fixes propagate only as fast as users check manually, so a
serious fix needs an out-of-band announcement channel.

### Deferral cost

Low until Phase 6, with one exception worth acting on early: the *update package
format and manifest schema* should be settled before Phase 6 begins, because
retrofitting a signature envelope onto a shipped format means supporting two
formats forever. Everything else — certificate purchase, HSM setup, CI signing —
can wait, and is better decided with real numbers than in advance.

The one thing that must not slip: the first artefact handed to anyone outside the
project must be signed. An unsigned build in circulation, even briefly,
establishes exactly the habit this decision exists to prevent.

## Related

- [ADR-0013-installer-technology.md](ADR-0013-installer-technology.md) — the
  installer must support signing and preserve user data across updates
- [ADR-0022-msix-distribution.md](ADR-0022-msix-distribution.md) — Option C
  depends entirely on that decision
- [ADR-0020-plugin-and-skill-signing.md](ADR-0020-plugin-and-skill-signing.md) —
  the same trust question for skills, one layer down
- [ADR-0002-sqlite-single-source-of-truth.md](ADR-0002-sqlite-single-source-of-truth.md)
  — schema-version compatibility constrains what an update may do
- [SECURITY.md](../../SECURITY.md) — supply chain and release security
- [THREAT_MODEL.md](../../THREAT_MODEL.md) — supply-chain threat group:
  unsigned update, tampered model file, malicious dependency
