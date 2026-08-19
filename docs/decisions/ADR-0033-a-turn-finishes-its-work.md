# ADR-0033 — A turn finishes its work before it answers

- **Status:** Accepted
- **Date:** 2026-08-06
- **Supersedes:** nothing. Extends the bounded tool loop of PRD FR-123.

## Context

Three sessions in one evening, all the same complaint, all with the audit log
disagreeing with what the owner was told.

```
Sir: close MS edge
Jarvis: I see there's a Microsoft Edge window open (win-d8a7c59e).
        I'll close it for you.
[the turn ended here; only window.list had run]

Sir: did you close it?
Jarvis: Nope, it's still there. That Edge window is still open and even maximised.
```

```
Sir: open YouTube music and play whatever song is in the queue.
Jarvis: YouTube Music is now open and playing the current song from the queue, Sir.
[app.open ran and was verified. Nothing else ran. The song did not play.]
```

The second exchange is the one that decided this ADR. Asked directly, the model
looked and reported the truth. It had the tools, it had the information, and it
had already been told in the system prompt not to claim things it had not done.
What it did not have was any reason to keep going, because the loop ended the
moment it produced text instead of a tool call — a model that announced an
intention got exactly the same treatment as one that finished the job.

The owner's instruction was explicit: *"how about you allow it multiple llm
calls until it really knows... unless for sure task not done, dont stop
working"*, and named the intended end state — something closer to an agent
working a task across the whole machine than a chat turn that answers once.

## Decision

**A turn continues while its own reply describes work that nothing did.**

After the model stops proposing tools, the turn asks whether the reply is
finished business. Three shapes say it is not, and they are one situation seen
from different angles:

1. **A promise.** *"I'll close it for you."* Not a completion claim — nothing is
   claimed done — and true at the moment it is said. It becomes false only when
   the turn ends without keeping it.
2. **A completion claim with nothing behind it.** *"Done, Sir"* with no verified
   tool in the turn.
3. **A claim about a different action than the one performed.** *"...is now open
   and playing"* with a verified `app.open` and nothing that can play anything.

When any of those hold, the engine appends its own record of what has and has
not changed and lets the model continue, up to `MAX_FOLLOW_UPS` times. The
message states the facts and asks for the tool call or a plain refusal. It
deliberately does **not** name which tool to use: the model can already see the
catalogue, and naming one would move planning into the engine.

**Claims are checked against tools that could have produced them.** A verified
result licenses a claim only if the verified tool is one that could have done
*that* action (`CLAIM_EVIDENCE` in `jarvis.llm.grounding`). "Did any tool verify
anything?" was the old test and it passed in both failures above — a listing had
verified a listing, and an open had verified an open.

**An unrecognised tool is never contradicted.** The mapping is a closed list, so
a verified tool it has not heard of means *cannot tell*, never *did not happen*.
Hedging true replies is how a warning stops being read.

**The bound stays.** `MAX_TOOL_ROUNDS` rises from 8 to 12 and follow-ups are
capped at 3. When they run out, the reply is rewritten to say the work did not
happen. A loop that exits only on success is a hang wearing a helpful
expression, and FR-123 forbids it besides.

## Consequences

**Turns cost more.** A request that needs pushing costs extra model calls; the
owner has said cost is not the constraint and continuous working is. A turn that
finished cleanly is unaffected — the check is only reached when the reply itself
says something nothing backs.

**Two thresholds, on purpose, and they disagree.** Continuing uses a wider net
than rewriting. Pushing back on a finished turn costs one model call and an "it
is already done"; rewriting a true sentence tells the owner something false. So
the continuation trigger is eager and the rewrite stays conservative, and
`_SOUNDS_FINISHED` (engine) is deliberately blunter than `CLAIM_EVIDENCE`
(grounding).

**Every follow-up is still fully permissioned.** Continuation produces tool
*proposals*, and every one goes through `ToolInvoker`'s six checks. A turn that
carries on cannot do anything a first-round call could not; it will ask for
approval again, because that is what the invoker does. Nothing here creates a
path from a plan to an effect that did not already exist — which is the property
that made this safe to build at all.

**It cannot make the model competent.** This stops a turn ending on an unkept
promise. It does not make the model choose the right tool, and if the model
cannot do the job it will now say so after three attempts instead of one. That
is a better failure, not a success.

**A closed list has a next gap.** `CLAIM_EVIDENCE` covers the current tool set.
Every tool added from here needs an entry, or claims about it will go unchecked
in one direction and unrecognised in the other. This is a maintenance cost taken
knowingly, in exchange for a mechanism that is exactly as good as its visible
entries rather than one that is subtly wrong everywhere.

## Alternatives considered

**Prompting alone.** The system prompt already said not to claim what had not
been done. It was not enough on any of the three occasions, and a rule the model
can decline is not a control.

**Ending the turn and letting the user re-ask.** That is what happened, and it
is what the owner is objecting to. It also worked: the second exchange got the
truth. Requiring the user to notice and re-ask is asking them to be the check.

**Rewriting only, without continuing.** Honest and insufficient. It produces an
accurate account of a job that did not get done; the point is to do the job.

**Unbounded looping until verified.** Directly forbidden by FR-123, and wrong
regardless: a task that cannot succeed must terminate and say so.
