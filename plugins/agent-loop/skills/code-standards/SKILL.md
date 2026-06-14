---
name: code-standards
description: Engineering standards every code-writing tick must follow so the loop produces GOOD code, not just working code. Invoked by build/maintenance ticks before and while editing code. Composes with (never overrides) the host project's CLAUDE.md / AGENTS.md.
---

Write code a senior engineer would approve — not just code that passes. Apply on every build/maintenance tick
that touches code. These are the floor; the host project's `CLAUDE.md` / `AGENTS.md` wins on any conflict.

## 1. Think before coding
State your assumptions. If the goal has multiple readings, pick the simplest that fits and say which — don't
silently guess. If a simpler approach exists, take it. Surface real tradeoffs in the journal, up front.

## 2. Simplicity first
The minimum code that solves the *stated* goal — nothing speculative. No abstractions for single-use code, no
"flexibility"/config nobody asked for, no error handling for impossible states. If 200 lines could be 50, write
50. Test: *would a senior engineer call this overcomplicated?* If yes, cut it.

## 3. Surgical changes
Touch only what the goal needs. Match the surrounding style even if you'd do it differently. Don't refactor what
isn't broken or "improve" adjacent code/comments/formatting. Remove only the orphans YOUR change created; mention
pre-existing dead code, don't delete it. **Every changed line traces to the goal.**

## 4. Goal-driven + verified
Turn the task into a checkable success criterion (a test, a passing command). Write/extend the test, make it
pass; the suite is green **before AND after**. This feeds the forced verify gate — you cannot mark work done
without a real check (`backlog_done` requires a passing `verify` block).

## 5. Code intelligence
Prefer LSP (go-to-definition, find-references, types) over blind grep for navigation. After editing, verify
**no type/build errors** (`tsc --noEmit` / `cargo check` / the project's check) before claiming done.

## 6. Commits (if the loop commits)
Match the repo's existing commit style and conventions (message format, and whatever attribution/footer policy
the repo already uses — follow the project, don't impose one).

## Compose, don't override
If the host project has a `CLAUDE.md` / `AGENTS.md`, read and FOLLOW it — it takes precedence. This skill is the
baseline that travels with the framework (and applies on agents that don't read CLAUDE.md, like Codex).
