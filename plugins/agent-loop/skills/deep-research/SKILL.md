---
name: deep-research
description: AI-first investigative research using the orchestrator-worker pattern — decompose a question, fan out parallel subagent searches across multiple source angles, triangulate across independent sources, adversarially refute, synthesize a CITED answer with confidence, and loop until saturation. Use for open questions needing a well-supported answer. (For validating a hypothesis against data, use the experiment profile instead.)
---

Investigate an open question to a well-supported, **cited** answer. Modeled on the orchestrator-worker research
system (a lead plans → parallel subagents gather in their own contexts → lead synthesizes → a citation pass),
which beats single-agent research because breadth is parallelized and each angle is blind to the others.

## Procedure (AI-first, token-light)
1. **Decompose.** Break the question into independent sub-questions and list the **source modalities** to sweep —
   web, docs, codebase, data, primary sources. One angle alone always misses things.
2. **Sweep (fan out).** Spawn ONE subagent per sub-question/modality, **in parallel**. Each runs in its OWN
   context (the search burns the *subagent's* tokens, not yours) and returns only a small **structured findings
   list**: `{claim, source, confidence}`. They're blind to each other — that's the point.
3. **Triangulate.** A claim is "supported" only if **≥2 independent sources** agree. Single-source = `unverified`.
   Prefer primary sources; down-rank low-credibility ones. Note disagreements explicitly.
4. **Refute.** Run `/grill-ai` + `/doubt-driven-development` on the surviving claims — try to break each.
   **Confidence-filter**: verify a weak claim up, or drop it. Better 3 solid findings than 30 maybes.
5. **Synthesize.** Integrate into a coherent answer with a **citation per claim** and a confidence level; honest
   `UNKNOWN — needs X` where evidence is thin. A report, not a link dump.
6. **Completeness critic.** Ask: what modality didn't I run? what claim is still single-source? what key source
   is unread? what contradiction is unresolved? Each gap becomes a targeted next sweep.
7. **Loop until saturation.** Repeat sweeps until **K rounds surface nothing new** (loop-until-dry). Record every
   settled finding in the `decided` ledger (`key=finding`) so later rounds never re-search the same ground.

## Rules
- Triangulate (≥2 independent) before asserting; cite every claim; confidence-scored; honest `UNKNOWN`.
- Parallel + subagent-delegated (token-light) — synthesis reads only the findings, never the raw search context.
- Refute BEFORE synthesis (attack findings, don't just confirm). Loop-until-dry, not one-shot.
- Record findings in the ledger so rounds don't repeat. AI-first; only HUMAN-GATE actions crossing a real gate.
