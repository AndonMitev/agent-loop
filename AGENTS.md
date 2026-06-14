# AGENTS.md — agent-loop for any agent (Claude Code, Codex, …)

agent-loop is **tool-agnostic at its core.** The engine is a plain Python helper + a JSON substrate + markdown
instructions — none of it depends on a specific agent. Claude Code gets native packaging (a plugin, slash
skills, a Stop hook); other agents (Codex) drive the same engine through this file.

## The portable contract
- **Helper:** `python3 .loop/loop.py` — `list / init / state / status / tail / check / append / rotate / rm /
  auto / stop`. Pure Python, no agent dependency.
- **State (the loop's whole memory):** `.loop/<id>/state.json` (hot) + `.loop/<id>/log.jsonl` (append-only).
- **Profiles:** `.loop/profiles.json` (research / experiment / build / maintenance) — cadence, gate, triggers.
- **Procedures (instructions any LLM follows):** `plugins/agent-loop/skills/*/SKILL.md` — `spawn-loop`,
  `loop-tick`, `deep-research`, `plan-decompose`, `self-evolve`, `author-skill`, plus the critique/verify skills.

## How a non-Claude agent (e.g. Codex) runs a loop
1. **Spawn:** read `spawn-loop/SKILL.md`, classify the goal into a profile, then
   `python3 .loop/loop.py init <id> <profile> "<goal>"`.
2. **Tick:** read `loop-tick/SKILL.md`, then each iteration: `loop.py state <id>` (+ `tail`, `check`) → run the
   profile's tick body (following the relevant SKILL.md) → `loop.py append <id>` with the JSON record.
3. The SKILL.md files are just instructions — read and follow them; you don't need Claude's `/skill` matcher.

## Autonomy per agent (self-firing without a human)
- **Claude Code:** the bundled `Stop` hook + `loop.py auto <id>` self-fires `/loop-tick` (in-session). Token-railed.
- **Codex / others / unattended:** there's no Stop hook, so drive ticks from **headless re-invocation** — a cron
  (or CI) firing the agent's exec mode on `loop-tick <id>` (e.g. `codex exec`, `claude -p`). This is also the
  cheapest mode (fresh process per tick, zero context carry-over). `state.dispatch` tells the scheduler the
  cadence (`loop`/`schedule`/`event`).

## Interop
The substrate is the shared contract: state is plain JSON written only through the helper, so different agents can
even drive the *same* loop (one spawns, another ticks) — they read/write the same `state.json` + `log.jsonl`.

## Other agents (Windsurf, Cursor, Cline, opencode, …)
This file IS the universal adapter. Any agent that reads `AGENTS.md` (Codex, opencode, and a growing list) drives
the engine directly. For an agent with its own rules-file convention, the "adapter" is a one-liner pointing here:
- Cursor → `.cursor/rules/agent-loop.mdc`: "Follow `AGENTS.md`; use `python3 .loop/loop.py` + the `SKILL.md` procedures."
- Windsurf → `.windsurf/rules/agent-loop.md`: same one line.
- Cline → `.clinerules/agent-loop.md`: same one line.

Scope: **Claude Code and Codex are first-class** (native plugins). Everything else works through this file with
zero or one line of glue — the engine never changes, only the entry-point filename does.
