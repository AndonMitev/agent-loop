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
     new data / anomaly → `/grill-ai` + a `critic` subagent + `/doubt-driven-development`)* → ACT (check preregs;
     bar-clear → flag human; deadline no-clear → tombstone). Pre-register any NEW threshold BEFORE peeking.
   - **build** — PICK the current milestone → IMPLEMENT via `/test-driven-development` → **VERIFY with a SEPARATE
     agent** running real checks (the builder never grades its own work) → FIX → INTEGRATE → mark milestone done.
   - **maintenance** — SCAN health signals (tests / types / lint / CVEs / TODOs / metrics) → PICK a backlog item
     → IMPLEMENT **surgically** (touch only what it needs) → **FULL existing suite must be green before AND after**
     (regression gate); on regression → revert, log why, do not ship.
4. **Journal + evolve** — pipe ONE record to the helper (never hand-edit the json):
   ```
   echo '{"observe":{…},"decide":{…},"act":{…},"next":"…"}' | python3 .loop/loop.py append <id>
   ```
   optional in `act`: `config` (merge), `prereg_add` / `prereg_resolve`, `backlog_add` / `backlog_done`.
   The helper stamps cycle+ts, updates `state.last`, and sets `state.next` — the directive the NEXT tick reads.
   **That is the re-evolution.**
5. **End with a one-line delta.** Re-schedule the next wake per the profile's cadence if self-pacing.

## Rules (carry across all loops)
- Context is scratch, files are truth: nothing critical lives only in your head.
- Pre-register thresholds BEFORE peeking; honest null = success; cut −EV, don't widen to chase.
- Guardrails are human-gated (real money, prod deploy, external publish, spending) — flag, don't fire.
- Durable verdicts (tombstone / promotion / validated finding) graduate OUT to the repo's journal + memory.
- Cost discipline: spend reasoning (subagents/skills) only when a trigger matches real new work.
