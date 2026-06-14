---
name: loop-tick
description: Run ONE tick of a self-evolving agent-loop. Reads the loop's JSON state (its entire prior context), executes the profile's tick body (experiment / build / maintenance), and journals one record that sets the next directive. Use when a loop's scheduled wake fires, the user says "/loop-tick <id>", "tick the loop", or "run the next iteration". A tick is a pure function: (state + new data) -> (action + new state + one record).
---

Run one tick of loop `<id>`. You are a **stateless** agent; the substrate is your only memory. A tick is
`(state.json + new data) -> (action + new state + one log record)`.

## Universal procedure (every profile)
1. **Read state — this is your entire prior context.**
   ```
   python3 .loop/loop.py state <id>
   python3 .loop/loop.py tail <id> 3
   python3 .loop/loop.py check <id>
   ```
   `state.next` is your directive; `state.gate` is what "good" means; `state.triggers` route the work.
2. **Evaluate triggers** against state + observed signal — run only the matched action (keeps ticks cheap).
3. **Run the profile's tick body** (from `state.profile`):
   - **experiment** — OBSERVE the signal → SCORE vs `state.gate`/`prereg` → CRITIQUE *(cost-gated: only on
     new data / anomaly → `/grill-ai` + a general-purpose subagent with an adversarial prompt, or your `critic`
     agent if the environment has one, + `/doubt-driven-development`)* → ACT (check preregs; bar-clear → flag
     human; deadline no-clear → tombstone). Pre-register any NEW threshold BEFORE peeking.
   - **build** — PICK the current milestone → IMPLEMENT via `/test-driven-development` → **VERIFY** with REAL
     checks the builder didn't write: a *deterministic mechanical* check (compile / test / run the command) is
     enough on its own; for *judgment-heavy* acceptance (does it read well? is it correct in spirit?) use a
     SEPARATE agent so the builder never grades its own work → FIX → INTEGRATE → mark milestone done.
   - **maintenance** — SCAN health signals (tests / types / lint / CVEs / TODOs / metrics) → PICK a backlog item
     → IMPLEMENT **surgically** (touch only what it needs) → **FULL existing suite must be green before AND after**
     (regression gate); on regression → revert, log why, do not ship.
4. **Journal + evolve** — pipe ONE record to the helper (never hand-edit the json). Build the JSON with
   `python3 -c` so quotes/newlines/unicode can't break it (a raw `echo '{…}'` is fragile):
   ```
   python3 -c 'import json;print(json.dumps({"observe":{...},"decide":{...},"act":{...},"next":"..."}))' \
     | python3 .loop/loop.py append <id>
   ```
   optional in `act`: `config` (merge), `prereg_add` / `prereg_resolve`, `backlog_add` / `backlog_done`.
   The helper stamps cycle+ts, updates `state.last`, and sets `state.next` — the directive the NEXT tick reads.
   **That is the re-evolution.**
5. **Decide DISPATCH for the next tick — schedule vs loop.** The test: *is there useful work to do right now
   whose result the next step needs?*
   - **YES → loop** — run the next tick immediately (no wait). Progress is bounded by your compute, not the world.
     (build mid-milestone; draining a fix backlog; refine-until-passing.)
   - **NO → schedule** — wait. Polling *fast* external state you can't be pushed (CI, a market, a deploy) →
     short interval (≲270s, stays in the cache window). Genuinely *idle / slow* signal → long interval (20–30m+)
     or **event** (wake on push: background-task completion, `Monitor` tailing a log, or a cron heartbeat).
   `state.dispatch` is the profile default; OVERRIDE per tick by what's actually true now (e.g. a maintenance loop
   is `event` when idle but flips to `loop` while draining fixes; an experiment loop is `schedule` but `loop`-bursts
   when new data lands). Persist the choice by adding a top-level `"dispatch": "loop"|"schedule"|"event"` to the
   append record (so `list`/`status` show the CURRENT mode).
6. **Fire the next tick YOURSELF — the loop is self-perpetuating (AI-first, no user in the inner loop).** Act on
   the dispatch you just chose; do NOT wait for the user to re-invoke `/loop-tick`:
   - `loop` → run the next tick **immediately, in this same turn** (continue working; don't stop). If a Stop-hook
     autonomous loop is armed (`loop.py auto`), do the tick's HEAVY work in a **subagent** and return only a small
     result — the session is reused across iterations, so keeping each turn tiny is what keeps the loop token-cheap.
   - `schedule` → schedule a self-wake to run the next tick after the interval: `ScheduleWakeup` (in-session,
     self-paced) or a cron (`CronCreate` / system cron / CI calling `/loop-tick <id>`, durable across sessions).
   - `event` → arm a wake on the signal: the `Monitor` tool tailing the relevant log/output, or a cron heartbeat.
   Only **stop and ask the human** at a real gate — real money, prod deploy, external publish, spending,
   destructive/irreversible ops. Everything else: decide and proceed.
7. **End with a one-line delta** (the byproduct of acting, not a substitute for it).

## Rules (carry across all loops)
- Context is scratch, files are truth: nothing critical lives only in your head.
- Pre-register thresholds BEFORE peeking; honest null = success; cut −EV, don't widen to chase.
- Guardrails are human-gated (real money, prod deploy, external publish, spending) — flag, don't fire.
- Durable verdicts (tombstone / promotion / validated finding) graduate OUT to the repo's journal + memory.
- Cost discipline: spend reasoning (subagents/skills) only when a trigger matches real new work.
- Token-light: read ONLY `state.json` + `tail` (never the whole log); cost-gate the critique; in an armed
  in-session loop, delegate heavy work to a subagent so the reused session context stays small. For long
  unattended runs, prefer a cron firing fresh `/loop-tick` processes (zero carry-over) over a long in-session burst.
