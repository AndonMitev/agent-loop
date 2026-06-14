# agent-loop

**Self-evolving autonomous loops for Claude Code.** Give it a one-line goal; it stands up a loop that observes,
acts, verifies, and journals — then **fires its own next tick** and re-evolves its directive each iteration.
You set direction; the loop runs itself. Pure prompts + a small substrate helper: **no API key, no build step,
no infra.** It rides your Claude Code plan.

## The one idea
A tick is a pure function:

> **`(state.json + new data) → (action + new state + one log record)`**

Each tick is a *stateless* agent. The substrate (`state.json` + `log.jsonl`) is the loop's entire memory between
ticks, so token cost per tick is bounded no matter how long history grows. The loop "evolves" because every tick
rewrites `state.next` — the directive the next tick reads first.

Only one thing changes by **type of work** — a *profile*. The loop primitive and substrate are identical for all:

| Profile | For | Gate ("what good means") |
|---|---|---|
| **experiment** | validate an idea vs a slow/noisy signal | pre-registered bar, frozen before peeking; honest null = success |
| **build** | construct from a milestone DAG | acceptance met **and a verifier separate from the builder** confirms |
| **maintenance** | keep an existing app healthy | full suite green **before and after**; no regression; surgical edits |
| **research** | investigate an open question | every claim triangulated across ≥2 independent sources, refuted, cited, confidence-scored |

## Install (Claude Code plugin)
```
/plugin marketplace add AndonMitev/agent-loop
/plugin install agent-loop@agent-loop
```
Then in any project: `/spawn-loop "<your goal>"`. On first run the helper is copied into that project's `.loop/`.

## Quickstart (install → first output)
```
/plugin marketplace add AndonMitev/agent-loop
/plugin install agent-loop@agent-loop
/spawn-loop "keep this repo green and tidy"
```
`/spawn-loop` classifies the goal, seeds `.loop/<id>/`, runs the first tick, and schedules the next — you don't
click through iterations. You'll see a loop appear:
```
$ python3 .loop/loop.py list
repo-health  [maintenance] event    cyc=  1  preg=0 todo=0  next: sleep until a health signal fires …
```
Inspect any loop with `python3 .loop/loop.py status <id>`; remove one with `python3 .loop/loop.py rm <id>`.

## Use
```
/spawn-loop "<goal>"             classify → seed → run first tick → self-schedule (one command, self-running)
/loop-tick <id>                  manually run an iteration (the loop does this itself; use to nudge/debug)
python3 .loop/loop.py list       every loop: profile, dispatch, cycle, open preregs, todo, next
python3 .loop/loop.py status <id>  one-screen view of a single loop
python3 .loop/loop.py rm <id>    delete a loop
```
See **[EXAMPLES.md](EXAMPLES.md)** for real runs of all three profiles (maintenance / build / experiment).

## Autonomy (AI-first)
The loop does not rely on you to drive each step — you give a goal and approve hard gates; it does the rest:
- **Self-firing.** Each tick chooses its `dispatch` and fires the next tick itself — `loop` continues now,
  `schedule` self-wakes via `ScheduleWakeup`/cron, `event` waits on `Monitor`/a signal. One `/spawn-loop` →
  a self-running loop.
- **Hands-off in-session loop (Stop hook).** Arm it with `python3 .loop/loop.py auto <id> [max]` and a `Stop`
  hook re-fires `/loop-tick` automatically — no user clicks at all — until the tick sets `dispatch` away from
  `loop`, `max` iterations (default 12) is hit, or `loop.py stop`. (Technique adapted from Anthropic's Ralph
  Wiggum plugin, MIT.) Inert unless armed.
- **AI second brain, not a human.** Critique is `/grill-ai` (the agent asks *and answers* from evidence) +
  `/doubt-driven-development`; errors are handled by `/debugging-and-error-recovery`. No human in the critique
  or recovery path.
- **ACT, don't ask.** The loop decides and proceeds. It stops to ask **only** at genuine human gates — real
  money, prod deploy, external publish, spending, or destructive/irreversible ops.
- **Durable autonomy.** For unattended survival across closed sessions, point a cron/CI at `/loop-tick <id>`
  (or graduate to Managed Agents). Self-paced (`ScheduleWakeup`) loops run while the session is alive.

## Triggers
Loops are condition-routed, not dumbly periodic. A trigger is a predicate over `(state, signal)` → action, at two
levels: **when** a tick fires (time / push) and **what** it does once awake (the matched action). Push exists for
harness-tracked events (background-task completion, the `Monitor` tool tailing a log); external state is polled on
the heartbeat. See each loop's `state.triggers`.

## Schedule vs loop (per-tick dispatch)
It's not one or the other per loop — each loop *oscillates*, decided at the end of every tick:

> **Is there useful work to do right now whose result the next step needs?**
> **YES → loop** (run the next tick immediately; bounded by your compute, not the world).
> **NO → schedule** (wait): fast external state you must poll → short interval (≲270s); idle / slow signal →
> long interval (20–30m+) or **event** (wake on push: task completion, `Monitor`, a cron heartbeat).

`state.dispatch` holds the profile default (`build → loop`, `experiment → schedule`, `maintenance → event`); each
tick overrides it by what's actually true (maintenance flips to `loop` while draining fixes; experiment
`loop`-bursts when new data lands).

## Token cost (it's cheap by design)
The framework is built to be low-token, and autonomy doesn't change that if you follow the rails:
- **Tiny per-tick read.** A tick reads `state.json` (~1KB) + `tail 3` — never the whole history. Cost per tick
  is bounded no matter how long the log grows (`rotate` folds old records to an archive).
- **No re-doing past work.** A tick sees only the tail, so the durable **`decided` ledger** in `state.json`
  (always read in full, survives `rotate`) carries what's settled: one line per item (`{key, verdict, why}`,
  deduped by key). Every tick checks it before acting and records new verdicts into it, so a tick many cycles
  later doesn't repeat killed or explored work. The ledger is the optimized journal — recall without re-reading logs.
- **Cost-gated thinking.** The expensive part (critique via `/grill-ai` + a subagent) runs *only* on new data /
  anomaly, not every tick. Idle ticks are nearly free.
- **Bounded in-session loop.** A `while true` in one session would accumulate context every iteration, so the
  Stop-hook loop is capped (`max` iterations) and each tick delegates heavy work to a throwaway subagent — the
  reused session grows only by small results. For long unattended runs, a cron firing fresh `/loop-tick`
  processes carries nothing over (each tick starts from the tiny `state.json`) — the cheapest mode.

Rule of thumb: tight bursts → in-session Stop-hook (convenient); long-haul → cron (cheapest).

## Staying lean & sharp (anti-bloat, anti-sloppy)
Two failure modes kill unattended loops — they're guarded explicitly:
- **Anti-bloat.** Ticks are stateless (read `state.json` + `tail`, never history); `rotate` bounds the log;
  heavy work is delegated to throwaway subagents; `plan-decompose` cuts speculative scope; `author-skill` only
  fires on a *proven recurring* need and never duplicates. And **`self-evolve` garbage-collects every pass** —
  removes unused/duplicate skills, merges overlaps, keeps the smallest capability set. Net capability, not count.
- **Anti-sloppy.** Nothing is marked done or journaled as a verdict until it passes the tick's **output quality
  gate**: frozen acceptance verified by a *real* check (not vibes); every claim backed by evidence
  (`file:line`/data/passing command); no overclaiming (honest `PARTIAL`/`UNKNOWN` over a confident guess);
  **confidence-filtered** (low-confidence findings are verified up or dropped, not asserted — kills false
  positives); judgment calls verified by a *separate* agent (the builder never rubber-stamps itself); terse output.

## Compatibility (Claude Code + Codex)
The engine is tool-agnostic: a Python helper (`loop.py`) + a JSON substrate + markdown instructions, none of which
depend on a specific agent.
- **Claude Code** — native: install as a plugin, `/spawn-loop` & `/loop-tick` skills, a `Stop` hook for in-session
  autonomy.
- **Codex (and other agents)** — drive the same engine via [`AGENTS.md`](AGENTS.md): call `python3 .loop/loop.py`
  and follow the `SKILL.md` procedures; for autonomy use headless re-invocation (`codex exec` / a cron) instead of
  the Stop hook.
- **Shared state** — `state.json`/`log.jsonl` are plain JSON written only through the helper, so different agents
  can drive the *same* loop. (Targeted at Claude + Codex; others work via `AGENTS.md` but aren't a focus.)

**Why the `.claude-plugin/` directory, if it's agnostic?** That name is *required* by Claude Code to discover and
install a plugin (`marketplace.json` + `plugin.json` live there) — it's the **Claude adapter**, two manifest files,
nothing more. The agnostic **engine** is `loop/loop.py` + `loop/profiles.json` + the `skills/*/SKILL.md`
instructions + the `.loop/` substrate (plain Python/JSON/Markdown, no Claude dependency). Codex's adapter is
`AGENTS.md`. One engine, one small adapter per agent — the `.claude-` prefix marks the adapter, not the framework.

## Honest limitations
- **Self-paced loops are session-bound.** In-session self-wake (`ScheduleWakeup`) runs only while the session is
  alive. For unattended survival across closed sessions, drive `/loop-tick <id>` from a cron/CI job (or Managed
  Agents) — same loop, durable clock.
- **Verification is yours to ground.** The framework gives you the *places* to verify (the build profile's
  separate-verifier step, the maintenance regression gate) — the checks themselves must run real tests/builds.

## How it's laid out
```
.claude-plugin/marketplace.json        # makes this repo a Claude Code marketplace
plugins/agent-loop/
  .claude-plugin/plugin.json
  skills/spawn-loop/SKILL.md           # classify goal → seed a loop
  skills/loop-tick/SKILL.md            # run one iteration
  loop/loop.py                         # the substrate helper (deterministic, schema-enforcing)
  loop/profiles.json                   # the three work-type profiles
```

## Companion skills (bundled)
The loop tick calls these, vendored into the plugin so it works out of the box:
- **Original, AI-first** — `grill-ai` (AI-to-AI critique second brain), `plan-decompose` (autonomous goal →
  verifiable milestone DAG), `deep-research` (orchestrator-worker investigation: parallel sweep → triangulate →
  refute → cited synthesis → loop-until-saturation), `self-evolve` (the loop improves its *own* gate/triggers/
  profile and graduates lessons to memory), `author-skill` (the loop **writes new skills itself** when a step
  recurs, and wires them into the flow — no human review).
- **From [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT)** —
  `doubt-driven-development`, `test-driven-development`, `debugging-and-error-recovery`.

The loop is **self-extending**: via `self-evolve` + `author-skill` it grows its own capabilities as it runs.
See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for attribution.

## License
MIT © Andon Mitev. Bundled third-party skills under their own MIT licenses — see THIRD_PARTY_NOTICES.md.
