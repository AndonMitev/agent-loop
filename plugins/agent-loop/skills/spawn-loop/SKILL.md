---
name: spawn-loop
description: Stand up a self-evolving autonomous loop from a one-line goal. Classifies the work-type into a profile (experiment / build / maintenance), seeds the AI-first JSON substrate via .loop/loop.py, and sets the first directive. Use when the user says "spawn a loop", "/spawn-loop", "set up an autonomous loop", or hands you a goal to pursue continuously. The entry point of the agent-loop framework.
---

Stand up one self-evolving loop from a single goal. You do the classification; `.loop/loop.py` does the
deterministic substrate write. Intelligence in the skill, determinism in the helper.

## Step 0 — ensure the substrate is installed in THIS project (idempotent)
The helper + data live in the project's `.loop/` (per-project memory). If it isn't there yet, seed it from the
plugin bundle, then always call `python3 .loop/loop.py`:
```
[ -f .loop/loop.py ] || { mkdir -p .loop && cp "$CLAUDE_PLUGIN_ROOT/loop/loop.py" "$CLAUDE_PLUGIN_ROOT/loop/profiles.json" .loop/ ; }
```
(When developing the framework in-repo, `.loop/loop.py` already exists and this is a no-op.)

## Procedure
1. **Classify the work-type** from the goal into exactly one profile (read `.loop/profiles.json` if unsure):
   - **experiment** — validate an idea against a slow/noisy external signal; watch-and-judge; honest null = success.
     (e.g. "test whether signal X predicts Y", "does strategy Z have edge").
   - **build** — construct something toward a goal from a milestone DAG; fast local feedback; ship it.
     (e.g. "build feature/app/integration X").
   - **maintenance** — keep an existing app healthy; self-source work from its own signals; regression is the risk.
     (e.g. "keep repo green", "maintain/improve the dashboard").
   - **research** — investigate an OPEN question to a cited, well-supported answer (orchestrator-worker sweep).
     (e.g. "what's the best X for Y", "find prior art on Z"). Distinct from experiment, which validates a
     hypothesis against data.
2. **Pick a short kebab-case id** for the loop (e.g. `dash-health`, `idea-xyz`).
3. **Init the substrate** — deterministic, do NOT hand-write the json:
   ```
   python3 .loop/loop.py init <id> <profile> "<goal>" [--deadline YYYY-MM-DD]
   ```
   (`--deadline` for experiment/build loops with a verdict date.) This seeds `state.json` from the profile
   (cadence / gate / triggers / first directive) and writes cycle 0 to `log.jsonl`.
4. **Pre-register up front** (experiment loops especially): if there's a kill/keep bar, append it BEFORE any
   data via a first tick's `act.prereg_add`. For build/maintenance, seed the backlog via `act.backlog_add`.
5. **Launch it autonomously — AI-first, no user in the inner loop.** Immediately run the first tick yourself via
   `/loop-tick <id>`; do NOT wait for the user to invoke it. From there the tick self-perpetuates (it fires its
   own next tick per its dispatch — see loop-tick step 6). One `/spawn-loop` call yields a *self-running* loop.
   For tight in-session bursts (e.g. a build draining a milestone), arm the Stop-hook loop so it keeps ticking
   with zero user input: `python3 .loop/loop.py auto <id> [max]` (default max 12). It auto-stops when the tick
   sets `dispatch` away from `loop`, when `max` is hit, or on `python3 .loop/loop.py stop`. Token rail: the cap +
   the dispatch self-stop bound it; keep each tick cheap (delegate heavy work to a subagent, cost-gate critique).
   `max` bounds the in-session **burst, not the work**: if it caps with work still remaining, the helper says so
   loudly and the loop stays fully resumable from `state.next` — continue with another `loop.py auto <id>` or a
   cron. For work that won't fit one burst, prefer cron mode (fresh `/loop-tick` per tick, no cap needed).
6. **Cadence / durability.** The loop self-schedules per its `dispatch`: `loop` → continue now; `schedule` →
   `ScheduleWakeup` (in-session, self-paced) or a cron; `event` → `Monitor`/cron on a signal. Self-paced loops are
   session-bound; wire a cron (`CronCreate` / system cron / CI calling `/loop-tick <id>`) for unattended survival.
   State the cadence + durability you chose.

## Output
Terse: the id, profile, gate, first directive, and the chosen cadence. Then hand off to `/loop-tick`.

The loop's whole memory is `.loop/<id>/{state.json,log.jsonl}`; every write goes through `loop.py` (no drift).
`python3 .loop/loop.py list` shows all loops.
