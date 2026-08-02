# ADR-0007: Ollama Loopback-Only Trust Boundary

- **Status:** Accepted, with a named residual risk
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §4.1, §7.4, §12.1, §13.4, NFR-021, AT-001
- **Phase:** 0

## Context

Project Jarvis routes conversation, planning, vision and embeddings through
a locally-hosted Ollama endpoint (PRD §12.1, default `127.0.0.1:11434`).
Ollama's HTTP API, by design and by default, has no authentication: any
process running as the same Windows user — or in some configurations, any
process on the machine at all — that can reach the configured port can talk
to it exactly as Jarvis does. This is not a bug in Ollama and not something
Project Jarvis can fix from the outside; it is a property of the local model
runtime the product has chosen to build on (PRD §12.1's "Recommended stack").

Two separate concerns follow from this, and they need separate treatment.
First, the *destination*: the PRD requires local AI inference to stay local
by default (PRD §4.1 "Local first, not local only"; §7.4 defines Offline,
Local assistant, and Connected modes explicitly) and requires that no
network request happen in offline mode at all (AT-001). If the configured
"local" endpoint were ever, through misconfiguration or a compromised
setting, actually a remote host, every prompt — potentially containing
personal context — would silently leave the machine. Second, the *source*:
because the endpoint is unauthenticated, Jarvis cannot prove that the
process answering on port 11434 is really Ollama and not something else
squatting the port.

## Options considered

### Option A — Loopback-only enforcement at the adapter boundary, output still treated as untrusted (chosen)
**Pros:** Directly closes the "silently remote" failure mode by refusing to
even open a connection to a non-loopback host; makes AT-001 a structural
property of the code rather than a matter of caller discipline, since the
offline check happens in the same boundary that would otherwise dial out;
combined with the six-step tool-invoker pipeline (PRD §13.4), it means that
even a malicious or spoofed response from whatever is listening on the port
still has to produce a schema-valid, permission-checked, lock-checked tool
call to do anything at all.
**Cons:** Does not authenticate that the loopback listener is actually
Ollama; a local process squatting the port is not detected.

### Option B — Trust the configured base URL as given, rely on caller discipline for offline mode
**Pros:** Simpler; no special-casing of host resolution.
**Cons:** AT-001 becomes a property of every call site remembering to check
network mode before calling the LLM adapter, rather than a property of the
adapter itself — exactly the kind of distributed responsibility that tends
to have one forgotten call site. A configuration mistake (or a future
integration pointing the base URL at a remote OpenAI-compatible endpoint
without updating the network-mode check) would silently ship prompts off the
machine. Rejected.

### Option C — Authenticate or pin the local Ollama endpoint (e.g. verify a token, pin by process, or run a local reverse proxy that adds auth)
**Pros:** Would close the "source" concern this ADR names as a residual
risk — a rogue local process could no longer plausibly impersonate Ollama.
**Cons:** Ollama's stock Windows distribution does not support this out of
the box; building it would mean either patching/wrapping Ollama (fragile
across Ollama updates) or running a local authenticating proxy in front of
it (additional moving part, additional process, additional attack surface of
its own, for a threat — another process on the same user account — that
already has substantial access to the user's session regardless). Not
adopted now; recorded below as the open follow-up rather than dismissed.

## Decision

- **The configured Ollama base URL must resolve to a loopback address** or
  the adapter refuses to connect and audits the refusal. This check happens
  in the adapter itself, not in callers, so a remote "local" endpoint cannot
  silently ship every prompt off the machine regardless of how the base URL
  was set.
- **Offline mode is enforced at the adapter boundary, not by caller
  discipline.** In `offline` network mode, the health check (and, when
  implemented, every LLM call) does not open a socket at all; it returns a
  `skipped(reason="offline_mode")` result. This is what makes AT-001 a
  property of the adapter rather than an emergent property of every caller
  behaving correctly.
- **All model output is treated as untrusted input**, regardless of how
  much the loopback check narrows where it could have come from. Model
  output must pass the full six-step invoker pipeline — schema validation,
  permission evaluation, resource-lock evaluation, tool allow-list
  validation, parameter validation, and approval where required (PRD
  §13.4) — before it can have any effect. The loopback restriction reduces
  *who could plausibly be answering*; it does not upgrade the trust level of
  *what they say*.

## Enforcement

- The health checker (`jarvis.llm`, ARCHITECTURE.md §6.8) rejects a
  configured base URL whose host is not a loopback address and writes an
  audit event recording the refusal; this is exercised by tests that assert
  a non-loopback base URL never results in a socket being opened.
- The offline-mode short-circuit is a check at the top of the adapter's call
  path, before any network primitive is invoked, so `offline` mode cannot be
  bypassed by a component that forgets to check the current network mode
  itself.
- The requirement that model output pass all six invoker steps is enforced
  structurally by ADR-0003 and the tool invoker (ARCHITECTURE.md §6.6): there
  is no code path from "text the model produced" to "action taken" that
  skips the invoker, so this protection does not depend on the LLM adapter
  remembering to apply it.

## Consequences

### Positive
- A misconfigured or tampered base URL fails loudly (refusal + audit event)
  instead of silently exfiltrating prompts, satisfying NFR-021 ("local
  services must not accept remote connections by default" — the converse
  direction of the same discipline, applied to what Jarvis itself connects
  out to).
- AT-001 is testable directly against the adapter, without needing to audit
  every current and future caller for correct network-mode checking.
- Even in the worst case for this ADR — something else answering on the
  loopback port — the damage is capped by the same permission and approval
  machinery that governs every other tool call.

### Negative
- The loopback check adds a small amount of adapter-level complexity (host
  resolution and comparison) that a "just trust the configured URL" design
  would not need.
- Legitimate advanced configurations that might want Ollama running on
  another trusted machine on a private network (a real scenario for a
  household with a dedicated inference box) are not supported without an
  explicit, separately reviewed relaxation of this rule — which does not
  exist in Version 1.

### Residual risk
**This decision does not, and cannot, authenticate the Ollama endpoint
itself.** Ollama's local HTTP API is unauthenticated by design; any local
process — run by the same user, or in some Windows configurations any
process with network access to loopback — can bind to or intercept traffic
to the configured port. A rogue local process could squat the port and
return malicious tool-call proposals shaped to look like legitimate model
output. The only mitigation Version 1 has for this is that everything such
a response could propose is still permission-checked, lock-checked and
schema-checked by the invoker before it can run — the same protection that
applies to a genuinely malicious or hallucinating real model. Project Jarvis
does not currently detect or prevent endpoint squatting, and this is stated
here rather than discovered later.

## Revisit when
- Ollama or the Windows platform gains a practical local authentication
  mechanism (named-pipe binding, per-process ACL, or similar) that Option C
  could build on without a fragile proxy.
- A credible threat model finding (THREAT_MODEL.md) escalates the priority
  of endpoint squatting above its current "mitigated by downstream checks
  only" status.
- Multi-machine or remote-Ollama configurations become an explicit product
  requirement, at which point this ADR's loopback-only rule needs a
  deliberate, separately audited relaxation — not a quiet configuration
  change.

## Related
- ADR-0003 (closed capability set — the downstream control that bounds the
  damage of a spoofed endpoint).
- ARCHITECTURE.md §6.8 (model routing and the LLM boundary), §13 gap 1.
- PRD §7.4 (offline / local assistant / connected mode definitions), §13.4
  (model output pipeline).
- THREAT_MODEL.md.
