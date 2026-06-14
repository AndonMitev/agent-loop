---
name: author-skill
description: AI-first authoring of a NEW agent skill, autonomously (no human review). Used by self-evolve when a manual step recurs across loop cycles — writes a correctly-structured SKILL.md with frozen, checkable, AI-first instructions, places it in the skills dir, validates it, and wires it into the flow so the loop invokes it next time. Use when the loop identifies a proven recurring pattern worth turning into a reusable capability.
---

Grow the loop's OWN capabilities: turn a recurring manual pattern into a reusable skill — autonomously, no human
review. (This is the AI-first counterpart to human "write-a-skill" tools that stop to interview you.)

This is the loop **writing its own tools** — the sharpest expression of the `loop-tick` Prime directive (the driver
acts, it doesn't wait for capabilities to be handed to it). When a step recurs, the loop manufactures the skill and
wires it in, so next time it's one call. That self-extension is what lets one loop scale into many.

## When
Invoked by `/self-evolve` (or directly) once a step has recurred across **several** ticks and is stable enough to
freeze. Never author for a one-off — that's premature abstraction.

## Procedure (fully autonomous)
1. **Name + triggers.** Short kebab-case name; a one-line `description` ending with explicit "Use when …" triggers
   (that's how the runtime matches it). One skill = one capability.
2. **Write `SKILL.md`** in the project skills dir (`.claude/skills/<name>/SKILL.md`):
   - frontmatter: `name` + `description` (with triggers);
   - body: a numbered **PROCEDURE** of FROZEN, checkable steps (a *different* agent could follow it and not
     diverge) + a short **RULES** block. AI-first: the skill ACTS / asks-and-answers itself; never "ask the user"
     except at a real human gate. Reference the substrate/helper where relevant.
3. **Validate.** Frontmatter parses; every step is concrete and checkable (no hand-waving); no human-in-the-loop
   except real gates; it doesn't duplicate an existing skill (extend/compose instead). If a step isn't checkable,
   sharpen it.
4. **Wire it into the flow.** Reference the new skill from the relevant profile/tick step (or note it under
   `state.config.skills`) so the loop actually invokes it. A brand-new `SKILL.md` registers as an invocable
   `/command` on the next session; mid-session, invoke it by reading + following the file directly.
5. **Journal** the new capability (name + why) via the helper; `self-evolve` graduates notable ones to memory.

## Rules
- Author from a PROVEN recurring need, not speculation. Frozen, checkable, AI-first instructions matching the
  existing skills' shape. Don't duplicate — compose. No human review path.
