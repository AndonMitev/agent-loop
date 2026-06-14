---
name: self-evolve
description: AI-first retrospective that evolves the LOOP ITSELF — extracts durable lessons from recent cycles, updates the loop's gate/triggers/dispatch when a pattern proves out, graduates verdicts to the repo journal + memory, and autonomously AUTHORS a new skill when a manual step keeps recurring. No human in the loop. Use periodically (every N cycles) or at a verdict / tombstone.
---

The meta-loop: improve the loop's **own machinery** from its own history — autonomously. A normal tick evolves
`state.next`; self-evolve evolves the gate, the triggers, the profile, the memory, and even the skill set.

This is the loop **upgrading itself** — the trait that makes it feel like an autonomous intelligence rather than a
script: it gets sharper the longer it runs. It is a standing obligation of the driver (see the `loop-tick` Prime
directive: decide + act, invoke skills, grill at distinctions), not optional polish. A loop that never evolves is
just a cron.

## Procedure (fully autonomous)
1. **Read history for PATTERNS, not anecdotes.** `loop.py tail <id> N` + `state`. Look across cycles: what
   repeatedly worked, failed, or surprised. One-off noise is not a pattern.
2. **Extract DURABLE lessons** — the ones true beyond this single loop.
3. **Evolve the machinery** (only on a pattern with ≥ a few cycles of evidence):
   - Gate / `dispatch` default / triggers mis-set? Update via `act.config` and record the evidence + why.
   - A verdict reached (bar cleared / tombstone)? **Graduate it OUT** to the repo's journal + a memory file,
     and `prereg_resolve` it. Loop-local noise stays in the log; durable truth leaves the loop.
   - **A manual step recurred across several ticks?** Don't rely on noticing it — the trigger is **mechanical**:
     `loop.py status` / `check` surface any `AUTHOR-SKILL` candidate (a `manual_step` signature seen ≥3× that isn't
     yet a `config.skill`). For each one, run `/author-skill` to write the skill autonomously, wire it in, and add
     its name to `config.skills` (which clears the trigger). *This is the self-evolution*: the loop grows its own
     capabilities instead of repeating itself. (No human review — `/author-skill` is AI-first.)
4. **Prune — anti-bloat (do this EVERY self-evolve, not just when adding).** Bloat is a failure mode: every
   dead skill, duplicate capability, or stale state line makes *every future tick* heavier and dumber.
   - Drop dead backlog items / resolved preregs; `loop.py rotate <id>` if the log is long (token rail).
   - **Audit the capability set**: remove skills not invoked across several cycles; **merge overlapping** ones;
     keep the *smallest* set that covers the work. Net capability, not gross count — prefer compose/merge over add.
   - If `author-skill` ever created something that duplicates an existing skill, delete the dupe and point callers
     at the original.
   - **Keep the `decided` ledger tight** — it's the loop's optimized recall (so ticks never re-read history): merge
     near-duplicate keys, summarize a cluster of related verdicts into one line, and graduate the long story to a
     memory file leaving a one-line pointer. The ledger should stay a scannable index, not a second log.
5. **Journal the evolution** as one record (what changed in the machinery + the evidence); set `state.next`.

## Rules
- Evolve on **patterns** (≥ a few cycles), not single events; an honest "nothing to evolve this cycle" is a
  success, not a failure.
- **Net / +EV over vanity metrics**: don't widen a gate to chase a loss; cut −EV, keep +EV.
- Durable lessons graduate OUT (journal + memory); keep the hot state small.
- Autonomous: no human review of the evolution. Only HUMAN-GATE changes that cross a real gate (real money,
  prod deploy, external publish, destructive/irreversible).
