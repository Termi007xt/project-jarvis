# ADR-0016: Custom "Jarvis" Wake Word

- **Status:** Accepted — per-user voice enrolment during onboarding (decided 2026-08-02)
- **Date:** 2026-08-01, decision recorded 2026-08-02
- **Deciders:** Project owner
- **PRD reference:** §25.6, FR-010, FR-011, FR-018; also §12.1, §16 item 9
- **Phase:** 1

## Context

FR-011 states the default product phrase shall be "Jarvis," and in the same
requirement prohibits the GUI from promising that a model trained for "Hey
Jarvis" will reliably detect "Jarvis" alone. openWakeWord ships pretrained models
for common phrases including "Hey Jarvis"; a bare single-word phrase is
materially harder to detect reliably, because shorter phrases have fewer
distinguishing phonetic features.

**No pretrained wake-word model file is present on the development machine.**
This was confirmed on 2026-08-02: `config/defaults.yaml` names the provider and
phrase, but no model artefact exists locally. Phase 1 therefore cannot simply
load a shipped model — it has to obtain one.

Two other things are now verified and change the calculus:

- faster-whisper `small` transcribes real microphone input correctly
  (`tools/voice-lab/test_whisper.py`).
- Kokoro `bm_george` synthesises correctly (`tools/voice-lab/test_kokoro.py`),
  which also implies espeak-ng is installed and functioning, since Kokoro needs
  it for English phonemisation.

So the speech stack is proven at both ends. The wake word is the one unproven
link.

## Options considered

### Option A — Train and ship one universal "Jarvis" model
Curated multi-speaker dataset, hard-negative training, false-activation evaluation.
**Pros:** works out of the box for every user; matches FR-011 literally.
**Cons:** substantial data-collection and training cost before *anyone* can use
the product; the trained artefact must then be licensed and distributed
(§17.2, §17.3), which is an unsolved problem for a model trained on collected voices.

### Option B — Ship the pretrained "Hey Jarvis" model as the permanent default
**Pros:** zero training cost; a verified artefact with known behaviour.
**Cons:** requires downloading a third-party model; does not satisfy FR-011's
stated default; a universal model is tuned for nobody in particular.

### Option C — Push-to-talk as the practical default
**Pros:** no false activations at all.
**Cons:** undercuts the voice-first framing; does not answer the question.

### Option D — Per-user voice enrolment during onboarding *(chosen)*
The user speaks their chosen wake phrase during first-run setup. Jarvis trains a
personal wake-word model from those recordings. The user can retrain it, or
enrol additional wake words later.
**Pros:** the model is tuned to the actual speaker, microphone and room, which is
where wake-word accuracy is really won. It sidesteps the distribution and
licensing problem entirely — a personally trained model never ships. It lets the
user choose "Jarvis", "Hey Jarvis", or something else, so FR-011's default
becomes achievable per user rather than universally. It makes §16 onboarding item
9 literal rather than aspirational.
**Cons:** first run becomes longer and involves an unavoidable recording step.
Enrolment quality varies with the user's care. It needs a real training pipeline
inside the product, not just an inference path. Accuracy must be *measured* after
enrolment, not assumed.

## Decision

**Option D.** Wake-word enrolment is a first-run onboarding step in Phase 1:

1. The user picks a wake phrase (default suggestion: "Jarvis"; "Hey Jarvis"
   offered as the easier alternative).
2. The user records a small number of samples of that phrase.
3. Jarvis produces a personal wake-word model from those samples.
4. Jarvis **measures** the result before enabling always-listening, and reports
   the measurement honestly.
5. The user can retrain, or enrol an additional wake word, at any time from the
   Voice settings screen.

Push-to-talk (**F9**, see ADR-0027 and PRD FR-018) remains available in parallel
and is the fallback whenever enrolment has not been completed or did not meet the
quality bar.

## Implementation path — Path 1 chosen for Phase 1 (decided 2026-08-02)

The naive reading — "train a wake-word model from scratch on a handful of user
recordings" — will not produce a usable detector. Two workable paths exist:

- **Path 1 — pretrained base + personal verifier.** *(chosen for Phase 1)*
  openWakeWord supports a *custom verifier model* trained on a small number of
  samples from a specific speaker, layered on top of a base wake-word model to
  cut false activations. This is exactly the few-shot, speaker-specific case, and
  it is the cheapest route to something that actually works.
- **Path 2 — synthetic augmentation.** *(deferred, revisit after Phase 1)*
  Generate a large synthetic positive set for an arbitrary phrase using TTS
  across many voices, mix with the user's real recordings and hard negatives, and
  train a full model. Supports a truly arbitrary phrase; a much larger piece of
  work needing a training environment inside the product.

### The consequence of Path 1: it constrains the phrase

Path 1 layers a personal verifier on a **pretrained base model**, so the wake
phrase in Phase 1 must be one for which a pretrained base exists. openWakeWord
ships a pretrained **"Hey Jarvis"** model. It does **not** ship one for the bare
word "Jarvis" — that is precisely the case Path 2 exists to serve.

Therefore, for Phase 1:

- The enrolled phrase is **"Hey Jarvis"**, personalised to the user's voice,
  microphone and room by the verifier.
- Bare **"Jarvis"** is **not** available and must not be offered as though it
  were. FR-011 explicitly forbids the GUI from implying that a model trained for
  "Hey Jarvis" detects "Jarvis" alone. The Voice screen must show the enrolled
  phrase truthfully and say that a single-word phrase requires the Path 2 work.
- Phase 1 must **obtain the base model** — no wake-word artefact exists on this
  machine. This is a concrete acquisition task, not an assumption, and it carries
  the disclosure obligations of PRD §17.2 (provider, licence, size, install
  location, removability).

This does not change the Option D decision. Per-user enrolment still happens, and
it still avoids redistributing a trained artefact — the personal verifier never
ships. It narrows *which phrase* Phase 1 can honestly deliver.

The honesty requirement in FR-011 stands regardless of path: the GUI must never
show a phrase as active that has not been enrolled and measured.

## Decision criteria

1. After enrolment, Jarvis reports a measured false-accept and false-reject
   indication from a held-out portion of the user's own samples plus a negative
   set. "We trained a model" without measurement does not satisfy this.
2. Always-listening is not enabled until enrolment passes the quality bar; below
   it, Jarvis says so plainly and falls back to push-to-talk.
3. Enrolment recordings are treated as personal data: stored in the vault, listed
   in the Voice screen, deletable, and excluded from normal exports.
4. Retraining and enrolling an additional phrase are both reachable from the GUI.
5. The GUI never displays a wake phrase as active unless its model is loaded.

## Consequences

### Positive
Accuracy is tuned to the real speaker and environment. No wake-word artefact
needs licensing or redistribution. FR-011's "Jarvis" default becomes reachable.
Onboarding item 9 becomes a real feature.

### Negative
Phase 1 grows: it now includes a training or verifier-fitting pipeline, an
enrolment UI, sample storage with its own privacy rules, and a measurement
harness. This is a genuine scope increase over "load a pretrained model" and
should be planned as such, not discovered mid-phase.

### Residual risk
Enrolment from few samples can still perform worse than a well-trained universal
model, particularly in noisy rooms or for a short single-word phrase. The
measurement gate in criterion 1 is what stops that from shipping silently.

## Revisit when
- Path 2 becomes worth building, which is what unlocks the bare "Jarvis" phrase
  FR-011 names as the product default. Expected after Phase 1, once enrolment and
  the measurement harness exist and can be reused.
- Measured enrolment quality is consistently poor across attempts.
- A licensable universal "Jarvis" model becomes available that outperforms
  per-user enrolment.

## Related
ADR-0027 (approval and activation interaction model — push-to-talk hotkey),
ADR-0028 (barge-in and full-duplex audio), ADR-0014 (voice licensing — the
parallel redistribution question that Option D avoids), PRD §12.1, §16 item 9,
FR-010, FR-011, FR-018.
