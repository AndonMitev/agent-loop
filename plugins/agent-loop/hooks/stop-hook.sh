#!/usr/bin/env bash
# agent-loop Stop hook — AI-first self-firing loop.
# Inert unless a loop is armed (.loop/.autoloop exists, written by `loop.py auto`).
# When armed, asks the deterministic helper whether to continue; if so, blocks exit and re-feeds
# /loop-tick <id>. Token rails live in the helper: bounded by max-iterations AND the tick's own
# dispatch decision (when the tick sets dispatch != "loop", the in-session burst ends).
set -euo pipefail
cat >/dev/null 2>&1 || true   # drain the hook's stdin payload (unused)

[ -f .loop/.autoloop ] || exit 0          # nothing armed -> normal exit
[ -f .loop/loop.py ]   || exit 0          # no helper in this project -> normal exit

RES="$(python3 .loop/loop.py autotick 2>/dev/null || true)"
case "$RES" in
  "CONTINUE "*)
    LID="${RES#CONTINUE }"
    # Block the stop and feed the next iteration's instruction back to Claude.
    python3 -c 'import json,sys; lid=sys.argv[1]; print(json.dumps({"decision":"block","reason":(
      "Autonomous agent-loop iteration. Run /loop-tick "+lid+" now. Read .loop/"+lid+"/state.json first "
      "(that is your whole context). Do heavy work in a SUBAGENT and return only a small result so this "
      "session stays token-light. Set dispatch=schedule|event in the append record when work runs out — "
      "that ends this in-session burst. Stop only at a human gate (real money / prod / publish / destructive)."
    )}))' "$LID"
    ;;
  *)
    exit 0                                 # STOP ... or empty -> allow exit
    ;;
esac
