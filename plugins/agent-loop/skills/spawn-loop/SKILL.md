---
name: spawn-loop
description: Stand up a self-evolving autonomous loop from a one-line goal. Classifies the work-type into a profile (research / experiment / build / maintenance), seeds the AI-first JSON substrate via .loop/loop.py, and sets the first directive. Use when the user says "spawn a loop", "/spawn-loop", "set up an autonomous loop", or hands you a goal to pursue continuously. The entry point of the agent-loop framework.
---

Stand up one self-evolving loop from a single goal. You do the classification; `.loop/loop.py` does the
deterministic substrate write. Intelligence in the skill, determinism in the helper.

**What you are spawning is an autonomous operator, not a cron job.** Once seeded it runs itself — observes,
decides, acts, grills its own conclusions, and rewrites its own next directive every tick. It should behave like
a relentless engineer who never needs to be told the obvious next step. The behavioral contract it lives by is
the **Prime directive** at the top of `loop-tick` (decide + act, never passive; invoke skills, don't describe
them; grill yourself at every real distinction). You set the goal and guard the hard gates; it drives.

## Step 0 — ensure the substrate is installed in THIS project (idempotent)
The helper + data live in the project's `.loop/` (per-project memory). If it isn't there yet, seed it from the
plugin bundle, then always call `python3 .loop/loop.py`:
```
[ -f .loop/loop.py ] || { mkdir -p .loop && cp "$CLAUDE_PLUGIN_ROOT/loop/loop.py" "$CLAUDE_PLUGIN_ROOT/loop/profiles.json" .loop/ ; }
```
(When developing the framework in-repo, `.loop/loop.py` already exists and this is a no-op.)

## Procedure
1. **Classify the work-type** from the goal into exactly one profile (read `.loop/profiles.json` if unsure).
   Natural lifecycle order — research → experiment → build → maintenance:
   - **research** — investigate an OPEN question to a cited, well-supported answer (orchestrator-worker sweep).
     (e.g. "what's the best X for Y", "find prior art on Z"). Distinct from experiment, which validates a
     hypothesis against data.
   - **experiment** — validate an idea against a slow/noisy external signal; watch-and-judge; honest null = success.
     (e.g. "test whether signal X predicts Y", "does strategy Z have edge").
   - **build** — construct something toward a goal from a milestone DAG; fast local feedback; ship it.
     (e.g. "build feature/app/integration X").
   - **maintenance** — keep an existing app healthy; self-source work from its own signals; regression is the risk.
     (e.g. "keep repo green", "maintain/improve the dashboard").
2. **Pick a short kebab-case id** for the loop (e.g. `dash-health`, `idea-xyz`).
3. **Init the substrate** — deterministic, do NOT hand-write the json:
   ```
   python3 .loop/loop.py init <id> <profile> "<goal>" [--deadline YYYY-MM-DD]
   ```
   (`--deadline` for experiment/build loops with a verdict date.) This seeds `state.json` from the profile
   (cadence / gate / triggers / first directive) and writes cycle 0 to `log.jsonl`.
4. **Pre-register up front** (experiment loops especially): if there's a kill/keep bar, append it BEFORE any
   data via a first tick's `act.prereg_add`. For build/maintenance, seed the backlog via `act.backlog_add`.
   **Define the success predicate** — the machine-checkable condition that means the goal is DONE — via
   `act.success_add:[{check,kind,desc}]` (`kind:"cmd"` = a shell check that exits 0, run by `loop.py` itself as
   an EXTERNAL oracle; `kind:"prereg"` = a named prereg resolved). A loop with no success predicate can never
   know it's finished and runs forever. `loop.py` lints out degenerate no-ops (`echo`/`true`/`:`), but only you
   can make it the RIGHT check — for a build it's the test/command that proves the feature; for an experiment
   it's usually the prereg-resolved-at-deadline; for research, a form-check over the `decided` ledger. When the
   goal may be met, a tick runs `loop.py done <id>`; all checks pass → the loop records a verified completion and
   terminates itself.
5. **Launch it autonomously — this is the default, AI-first, no user in the inner loop.** Arm autonomous mode
   and run the first tick yourself, immediately:
   ```
   python3 .loop/loop.py auto <id>      # on by default — the Stop hook re-fires /loop-tick with zero user input
   /loop-tick <id>                       # kick the first tick; from here it runs itself
   ```
   One `/spawn-loop` yields a loop that **runs itself** — each tick fires the next per its `dispatch`, and the
   armed Stop hook keeps it ticking hands-free. It self-stops only when the tick sets `dispatch` away from `loop`,
   the goal completes (`done`), the burst cap is hit, or you run `python3 .loop/loop.py stop`. The cap (`auto <id>
   [max]`, default 12) bounds one in-session **burst, not the work**: if it caps with work remaining, the loop
   stays fully resumable from `state.next` — re-arm with another `loop.py auto <id>` or a cron. For long unattended
   runs, drive a fresh tick per fire from cron. Keep each tick cheap (delegate heavy work to a subagent, cost-gate
   critique).
6. **Cadence / durability.** The loop self-schedules per its `dispatch`: `loop` → continue now; `schedule` →
   `ScheduleWakeup` (in-session, self-paced) or a cron; `event` → `Monitor`/cron on a signal. Self-paced loops are
   session-bound; wire a cron (`CronCreate` / system cron / CI) for unattended survival.
   **CRON PROMPT RULES (do NOT get this wrong — it's the #1 loop failure):**
   - **Never put `/loop-tick <id>` (a slash command) in a cron prompt.** Slash skills may not be registered in a
     headless/scheduled session → it fails with "Unknown command." Use a *natural-language* prompt that points at
     the helper + the SKILL.md file path instead.
   - **Never dump the loop's rules into the prompt.** The gates/constraints live in `state.gate` / `state.prereg` /
     `state.decided` — the prompt re-sending them every tick is the exact anti-pattern this framework kills.
   - **The prompt is short + stable; the dynamism is `state.next`.** Generate the right prompt with
     `python3 .loop/loop.py prompt <id>` (it embeds the live `state.next`, slash-free). System cron:
     `cd <repo> && claude -p "$(python3 .loop/loop.py prompt <id>)"`. Harness cron (static prompt): copy a short
     line like *"Run the next tick of '<id>': cd <repo>, `python3 .loop/loop.py state <id>`, follow
     .claude/skills/loop-tick/SKILL.md; honor state.gate/prereg/decided; this tick = state.next."*
   State the cadence + durability you chose.

## Output
Terse: the id, profile, gate, first directive, and the chosen cadence. Then hand off to `/loop-tick`.

The loop's whole memory is `.loop/<id>/{state.json,log.jsonl}`; every write goes through `loop.py` (no drift).
`python3 .loop/loop.py list` shows all loops.
