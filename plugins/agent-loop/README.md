# agent-loop (plugin)

Self-evolving autonomous loops for Claude Code. Pure prompts + a ~180-line substrate helper — no API key, no
build step, no infra. It rides your Claude Code plan.

## The one idea
A tick is a pure function: **`(state.json + new data) -> (action + new state + one log record)`**. Each tick is
a *stateless* agent; the substrate is the loop's entire memory between ticks. The loop "evolves" because every
tick rewrites `state.next` — the directive the next tick reads first.

## Contents
| Part | What | Where |
|---|---|---|
| **Substrate** | `state.json` (hot) + `log.jsonl` (append-only) per loop, written ONLY via the helper | project `.loop/<id>/` |
| **Helper** | deterministic schema writer: `init / state / tail / check / append / rotate / list` | `loop/loop.py` |
| **Profiles** | the only thing that changes by type of work | `loop/profiles.json` |
| **Skills** | `/spawn-loop` (classify → seed a loop) and `/loop-tick` (run one iteration) | `skills/` |

## Profiles
- **experiment** — validate an idea vs a slow/noisy signal; watch-and-judge; pre-registered bar; honest null = success.
- **build** — construct from a milestone DAG; fast feedback; *verifier separate from builder*.
- **maintenance** — keep an app healthy; self-sourced backlog; *full-suite regression gate*; surgical edits.

## Use
```
/spawn-loop "keep this repo green and tidy"   # → classifies → maintenance loop, seeds .loop/
/loop-tick <id>                               # one iteration: read state → work → journal → set next
python3 .loop/loop.py list                     # all loops at a glance
```
On first `/spawn-loop`, the helper is copied into your project's `.loop/` (per-project memory). Schedule the
cadence with ScheduleWakeup (self-paced) or a cron. **Loops are session-only** unless wired to a durable
scheduler — the one honest limitation.
