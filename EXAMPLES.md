# Examples

Three real flows — one per profile. These are abbreviated transcripts of actual `agent-loop` runs, not invented.

## 1. maintenance — "keep a repo green"
Self-sources work from the app's own health signals; the gate is *no regression*.
```
/spawn-loop "keep this repo green: tests compile and pass"
# → classified maintenance, seeded .loop/repo-health/

/loop-tick repo-health
#   tick body: SCAN health → run the suite (real check) → journal baseline
#   observed: strategy 31 + bots 52 + recorder 98 = 181 tests, 0 failed
#   gate met (green), backlog empty → dispatch=event (sleep until a signal)

python3 .loop/loop.py status repo-health
#   last : cycle 1  {"tests":{"total":181,"failed":0}}
#   NEXT : sleep until a health signal fires; on wake diff vs baseline_tests=181 → any drop = regression
```

## 2. build — "construct something" (this loop hardened agent-loop itself)
Milestone DAG, fast feedback, *verifier separate from builder*; dispatch stays `loop` until a milestone is done.
```
/spawn-loop "harden the agent-loop framework from real dogfooding"
# → classified build, seeded .loop/al-dev/

/loop-tick al-dev      # decompose → build → verify → journal, repeated
#   found 6 frictions by USING the tool; fixed 5 in one burst (dispatch=loop):
#     B1 list shows dispatch+todo   B2 status command   B3 robust append example
#     B4 verifier rule refined      B5 bundle companion skills (broken refs)
#   verified each with a real command run, then:

python3 -c 'import json;print(json.dumps({
  "observe":{"note":"found friction by using the tool"},
  "decide":{"verdict":"build-burst","why":"fix it now"},
  "act":{"change":"shipped the fix",
         "backlog_add":[{"id":"B1","want":"list shows dispatch","acceptance":"loop.py list prints dispatch"}],
         "backlog_done":["B1"]},
  "verify":{"check":"python3 .loop/loop.py list","result":"pass","evidence":"dispatch column now printed"},
  "dispatch":"schedule",
  "next":"work ran out -> wait"}))' | python3 .loop/loop.py append al-dev
#   backlog_done REQUIRES a passing verify block (the helper rejects "done" without proof)
#   when the work ran out, the tick flipped dispatch loop → schedule (it persists, shows in list)
```

## 3. experiment — "validate an idea" (fresh plugin install)
Watch-and-judge a slow signal; **pre-register the bar before peeking**; honest null = success.
```
/spawn-loop "does signal X predict Y" --deadline 2026-06-30
# → classified experiment, seeded .loop/demo/

# first tick pre-registers the kill/keep rule BEFORE any data:
python3 -c 'import json;print(json.dumps({"observe":{"fires":0},"decide":{"verdict":"keep"},
  "act":{"prereg_add":[{"id":"P1","trigger":"<20 fires by deadline","action":"honest null"}]},
  "dispatch":"schedule","next":"heartbeat; check P1"}))' | python3 .loop/loop.py append demo

python3 .loop/loop.py check demo
#   P1: IF <20 fires by deadline -> honest null
```

## The commands you'll actually use
```
/spawn-loop "<goal>"             classify → seed a loop
/loop-tick <id>                  run one iteration (read state → work → journal → set next + dispatch)
python3 .loop/loop.py list       all loops: profile, dispatch, cycle, open preregs, todo, next
python3 .loop/loop.py status <id>  one-screen view of a single loop
python3 .loop/loop.py check <id>   open pre-registrations + backlog
```
Every write goes through the helper (schema-enforced, no drift). The loop's whole memory is
`.loop/<id>/{state.json,log.jsonl}`.
