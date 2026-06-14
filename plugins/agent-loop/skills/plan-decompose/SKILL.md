---
name: plan-decompose
description: AI-first decomposition of a goal into a DAG of verifiable milestones with FROZEN acceptance criteria, written to a loop's backlog. No human — the agent derives milestones from the codebase/constraints, orders them by dependency, and freezes a checkable acceptance for each. Use at the start of a build loop, or whenever a goal needs breaking into executable steps.
---

Turn a goal into an executable, **verifiable** plan — autonomously, no human review. The output is a backlog of
milestones whose "done" cannot drift, because acceptance is frozen up front.

## Procedure (fully autonomous)
1. **Ground it.** Read `state.goal` + explore the actual codebase/docs/constraints. **Zoom out first** — map the
   relevant area before splitting, so the plan fits reality, not assumptions.
2. **Decompose into milestones** — each independently shippable, ordered by dependency (a DAG, not a wishlist).
   The *smallest* set that reaches the goal. No speculative scope.
3. **Freeze acceptance for EACH milestone BEFORE building** (mirrors pre-registration — the bar can't move after
   peeking): a concrete, checkable condition — a command that passes, a test, an observable output. If a
   milestone's acceptance can't be checked by a deterministic command or a separate agent, it isn't a
   milestone — split or sharpen it.
4. **Write the plan to the loop** in one append (never hand-edit the json):
   `act.backlog_add: [{ "id":"M1", "want":"…", "acceptance":"<checkable condition>" }, …]`, and set
   `next` to milestone 1's directive.
5. **Pick milestone 1** (respect the DAG) and hand off to the build tick.

## Rules
- Acceptance frozen BEFORE building; minimal scope (cut speculative work); evidence-grounded (derive from the
  real codebase, mark `UNKNOWN — needs X` rather than guessing); verifiable-only milestones.
- Autonomous: no human review. Only flag a milestone `HUMAN-GATED` if shipping it crosses a real gate
  (money / prod / publish / destructive).
