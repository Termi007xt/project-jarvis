# ADR-0016: Custom "Jarvis" Wake Word

- **Status:** Open — decision required before Phase 6
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §25.6, FR-010, FR-011; also §12.1, §16 item 9
- **Decision required before:** Phase 6 (public default wake phrase); Phase 1 proceeds on the documented interim phrase

## Context

FR-011 states the default product phrase shall be "Jarvis," and in the same requirement prohibits the GUI from promising that a model trained for "Hey Jarvis" will reliably detect "Jarvis" alone. `PROJECT_INPUTS.md` and `config/defaults.yaml` currently configure the honest interim state: `development_phrase: Hey Jarvis` is the pretrained openWakeWord-compatible model actually in use (`audio.wake_word.provider: openwakeword`, `phrase: "Hey Jarvis"`), with `desired_phrase: Jarvis` recorded separately as the unmet product target. This is not a contradiction to silently resolve — it is the honest gap PRD §4.6 ("honest task status") requires be named rather than hidden behind a GUI that quietly claims "Jarvis" works when only "Hey Jarvis" has been trained and verified.

The gap exists because openWakeWord ships pretrained models for common phrases including "Hey Jarvis"; a bare single-word wake phrase like "Jarvis" is materially harder to train reliably — shorter phrases have fewer distinguishing phonetic features, which tends to raise the false-activation rate unless a purpose-trained model with sufficient curated positive/negative audio is produced. PRD §12.1 lists both "Custom 'Jarvis' wake model if available or trained" and "Supplied 'Hey Jarvis' fallback" as stack components, and §16 onboarding item 9 already offers the user a choice between the fallback and custom training — the product design already anticipated this ADR's answer might be "both, user's choice" rather than a single forced default.

## Options considered

### Option A — Train a custom "Jarvis" model before public release
Produce a purpose-trained openWakeWord-compatible model for the bare word "Jarvis," using a curated positive dataset (multiple speakers, accents, recording conditions) and hard-negative training against acoustically similar words to control false-activation rate.
**Pros:** matches FR-011's stated default exactly; best user experience; differentiates the product.
**Cons:** real cost — data collection, training compute, and critically, credible false-activation evaluation before it can be trusted as a default (a wake model that mis-fires disrupts an always-listening assistant more than a slightly longer phrase costs); distribution/licensing of the trained model needs its own answer, since it is not a pretrained artefact with existing licence terms.

### Option B — Keep "Hey Jarvis" as the shipped default indefinitely; "Jarvis" only as opt-in/user-trained
Ship the verified pretrained "Hey Jarvis" model as the actual default; let FR-011's "trained custom wake-word model" option exist for users willing to train their own, without promising "Jarvis" alone out of the box.
**Pros:** no training/evaluation cost gates release; avoids ever shipping an unverified wake model; matches what §16 already frames as a choice.
**Cons:** does not satisfy FR-011's literal default-phrase requirement — choosing this option is choosing to formally amend FR-011 (a PRD deviation requiring its own record per §1.13), not merely deferring the question.

### Option C — Push-to-talk as the practical default, wake word secondary
Lean on FR-018's configurable global-hotkey push-to-talk as the primary activation method, with either wake phrase (A or B) available as an opt-in "always listening" enhancement.
**Pros:** sidesteps false-activation risk for users who prioritise reliability; formalises a fallback already present today (push-to-talk is `enabled` in parallel per `PROJECT_INPUTS.md`).
**Cons:** undercuts the "voice-first" product framing (§8.1 persona); does not itself resolve what the always-listening wake phrase should be, which most users will still want.

## Decision

Deferred. No option is selected yet. Phase 1 ships with the interim, honestly labelled state already configured: "Hey Jarvis" as the working, verified wake phrase, push-to-talk available in parallel (FR-018), and the GUI must not claim "Jarvis" alone is detected until Option A is actually completed and measured, per FR-011's explicit prohibition.

## Decision criteria

1. A custom "Jarvis" model, if trained, achieves a false-activation rate at or below the independently measured rate of the pretrained "Hey Jarvis" model under comparable test conditions — it must not merely "work sometimes," it must not regress reliability.
2. The GUI wake-phrase setting accurately reflects which phrase is actually active and verified, never displaying "Jarvis" as selected while only a "Hey Jarvis" model is loaded — a UI-honesty requirement independent of which option is chosen.
3. If a trained model is distributed to other users, its training-data licensing and any third-party voice-sample consent are documented, analogous to ADR-0014's voice-licensing gap but for a wake-word model rather than a TTS voice.
4. Push-to-talk remains available and discoverable regardless of which wake-phrase option is chosen, since FR-011 requires it as a fallback "when wake detection is unreliable" — not conditional on this ADR's outcome.
5. The cost of the false-activation evaluation harness itself (test audio corpus, methodology) is scoped and budgeted before committing to Option A, since "we trained a model" without credible measurement does not satisfy criterion 1.

## Consequences

### If Option A (custom training) is eventually chosen
Onboarding item 9 ("offer 'Hey Jarvis' fallback or custom wake-word training," §16) becomes literal rather than aspirational — a real trained-model artefact must exist, be distributed (bundled or downloaded per §17.2's disclosure requirements), and be kept in sync with openWakeWord's model format across upstream version changes.

### Deferral cost
Low through Phase 1–5: the interim "Hey Jarvis" configuration is fully functional and already the documented, verified default. The cost concentrates at the public-release boundary — Phase 6 cannot honestly market "say Jarvis" as the product's signature interaction until this ADR closes, and false-activation evaluation is cheaper to plan for early than to improvise under release pressure.

## Related

ADR-0014 (voice licensing — parallel redistribution question for a different asset type), PRD §12.1, §16 item 9, FR-011, FR-018.
