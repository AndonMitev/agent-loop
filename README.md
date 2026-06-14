# agent-loop

**Self-evolving autonomous loops for Claude Code.** Give it a one-line goal; it stands up a loop that observes,
acts, verifies, and journals — then re-evolves its own next directive each iteration. Pure prompts + a
~180-line substrate helper: **no API key, no build step, no infra.** It rides your Claude Code plan.

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

## Install

### Option A — native plugin (recommended)
```
/plugin marketplace add AndonMitev/agent-loop
/plugin install agent-loop@agent-loop
```
Then in any project: `/spawn-loop "<your goal>"`. On first run the helper is copied into that project's `.loop/`.

### Option B — clone + install into a repo
```
git clone https://github.com/AndonMitev/agent-loop
./agent-loop/install.sh /path/to/your/repo
```
Copies the skills into `.claude/skills/` and the substrate into `.loop/`, committed with your project.

## Use
```
/spawn-loop "keep this repo green and tidy"   # → classifies → maintenance loop, seeds .loop/
/loop-tick <id>                               # one iteration: read state → work → journal → set next
python3 .loop/loop.py list                     # every loop at a glance
python3 .loop/loop.py state <id>               # a loop's hot state (what a tick reads first)
```

## Triggers
Loops are condition-routed, not dumbly periodic. A trigger is a predicate over `(state, signal)` → action, at two
levels: **when** a tick fires (time / push) and **what** it does once awake (the matched action). Push exists for
harness-tracked events (background-task completion, the `Monitor` tool tailing a log); external state is polled on
the heartbeat. See each loop's `state.triggers`.

## Honest limitations
- **Session-only.** Loops tick on Claude Code's scheduler, which is tied to the session. For loops that survive a
  closed session, wire the tick to a durable scheduler (a cron/CI job, or graduate to Managed Agents).
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
install.sh                             # Option B installer
```

## License
MIT © Andon Mitev
