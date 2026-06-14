---
name: grill-ai
description: AI-to-AI relentless interrogation of a plan, design, or proposed change — the agent ASKS and ANSWERS each question itself from the codebase, data, journals, and memory (NO human in the loop), until every branch of the decision tree is resolved. Use inside autonomous loops, or when the user says "grill me but you answer", "AI communication", or "self-grill". The fully-autonomous variant of grill-me.
---

Relentlessly interrogate the plan / design / proposed change under review until shared understanding is
reached — but with **NO human**: you generate each question AND answer it yourself from evidence. This is
the autonomous, AI-to-AI variant of `grill-me` (which interviews a human). Never wait for a person.

## Procedure (fully autonomous)
1. **Frame the decision tree.** List the open questions / branches and their dependencies. Order them so a
   question is only asked after the questions it depends on are resolved.
2. **Walk it one question at a time** (depth-first, resolve dependencies first). For each question:
   - **ASK** it in its sharpest, most adversarial form (the Interrogator voice) — the version most likely
     to expose a wrong assumption. Do not soften it.
   - **ANSWER** it from EVIDENCE, not opinion: explore the codebase, read the journals / state docs, run
     the analysis tool (`arena`), or cite a memory slug. If the evidence does not exist, answer
     **"UNKNOWN — needs <X>"** and record exactly what would resolve it. **Never fabricate an answer.**
   - **RECORD** one dense line: `Q → A → decision · confidence · evidence(file:line / data / memory)`.
3. **Chase contradictions.** When an answer conflicts with an earlier one or with the data, follow the
   branch it opens. Continue until no remaining open branch would change the conclusion.
4. **Output** an AI-first transcript: the dense Q/A/decision list + a one-line **VERDICT** (and any
   `UNKNOWN`s that gate it). No prose padding — this is a machine working-record.

## Maximum independence (recommended in loops)
For true AI-to-AI separation, split the roles across agents: spawn a `critic` (or skeptic) subagent as the
**Interrogator** whose only job is to find the unresolved branch and refute the plan, while you act as the
**Answerer** defending each point from evidence. Iterate until the Interrogator runs out of live objections
or surfaces an `UNKNOWN — needs data`. This is the "second brain grills, the agent answers" pattern.

## Rules
- Evidence over opinion; an honest **UNKNOWN** beats a confident guess.
- Default skeptical — the Interrogator's job is to break the plan, not agree with it.
- Terse, machine-readable output; no human-readability padding.
- Never block on a human; if a decision is genuinely human-gated (real money, prod restart), record it as
  `HUMAN-GATED` and move on — do not stall the loop.
