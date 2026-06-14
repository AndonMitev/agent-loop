#!/usr/bin/env python3
"""agent-loop — project-agnostic self-evolving loop substrate (AI-first, token-light).

One primitive: a tick is a pure function `(state + new data) -> (action + new state + one log record)`.
The substrate IS the loop's memory between ticks; each tick is a stateless agent.

Per-loop artifacts under .loop/<id>/:
  state.json   HOT state: profile, goal, gate, triggers, open pre-regs, backlog, last reading, NEXT directive.
               Overwritten each tick. The ONLY thing a tick reads in full (tiny).
  log.jsonl    Append-only cycle history, one JSON record per line. Ticks TAIL it (never read whole).

Profiles (profiles.json) parameterize the loop by TYPE OF WORK — only cadence/tick-body/gate/triggers change.
The loop primitive and substrate are identical for every profile.

Commands:
  list                              all loops: id, profile, cycle, open pre-regs, next (truncated).
  init <id> <profile> "<goal>" [--deadline YYYY-MM-DD]
                                    create a loop, seed state from the profile, write cycle 0.
  state <id>                        print state.json — the machine view a tick reads FIRST.
  status <id>                        compact one-screen human summary (goal/gate/dispatch/preregs/backlog/next).
  tail <id> [N]                     last N log records (default 5) — context for a tick.
  check <id>                        list OPEN pre-registrations + deadlines.
  append <id>                       read one JSON record from stdin, stamp cycle+ts, append, update state.
                                      stdin schema: {"observe":{...},"decide":{...},"act":{...},"next":"..."}
                                      optional top-level "dispatch": "loop"|"schedule"|"event" (per-tick override)
                                      optional top-level "verify": {"check","result":pass|partial|fail,"evidence"}
                                        REQUIRED when the record marks work DONE (act.backlog_done or a done-ish
                                        verdict) -> append is REJECTED without a passing/partial verify. Forced.
                                      optional in "act": "config":{...}        -> merge into state.config
                                                         "prereg_add":[{id,trigger,action,deadline}]
                                                         "prereg_resolve":["P1"]
                                                         "backlog_add":[{id,want,acceptance}]
                                                         "backlog_done":["B1"]
                                                         "decided_add":[{key,verdict,why}]  -> durable ledger of
                                                            what's settled (dedup by key, survives rotate) so a
                                                            tick never re-does work that scrolled past the tail.
                                                         "manual_step":"<kebab-sig>"  -> tag a hand-rolled step
                                                            (sig = the skill name it would become). Counted; once
                                                            seen >=3x and not yet a config.skill, status/check
                                                            surface it as an /author-skill trigger. Mechanical.
  rotate <id> [KEEP]                fold all but the last KEEP records to log.archive.jsonl (default 50).
  rm <id>                           delete a loop (its whole .loop/<id>/ directory). Irreversible.
  auto <id> [MAX]                   arm AI-first autonomous mode: the Stop hook self-fires /loop-tick <id>
                                      until dispatch leaves 'loop', MAX iterations (default 12), or `stop`.
  stop                              disarm the autonomous loop (remove the pointer).
  autotick                          (internal) the Stop hook calls this to decide CONTINUE/STOP.

Prerequisite: python3 on PATH. No third-party packages.
"""
import json, os, sys, datetime, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
PROFILES = os.path.join(BASE, "profiles.json")
AUTOLOOP = os.path.join(BASE, ".autoloop")  # armed-autonomous-loop pointer (read by the Stop hook)


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def loop_dir(lid):
    return os.path.join(BASE, lid)


def paths(lid):
    d = loop_dir(lid)
    return d, os.path.join(d, "state.json"), os.path.join(d, "log.jsonl"), os.path.join(d, "log.archive.jsonl")


def load_profiles():
    return json.load(open(PROFILES)) if os.path.exists(PROFILES) else {}


def load_state(lid):
    _, s, _, _ = paths(lid)
    if not os.path.exists(s):
        sys.exit(f"no loop '{lid}' (run: loop.py init {lid} <profile> \"<goal>\")")
    return json.load(open(s))


def save_state(lid, st):
    _, s, _, _ = paths(lid)
    json.dump(st, open(s, "w"), indent=2, ensure_ascii=False)


def read_log(lid):
    _, _, lg, _ = paths(lid)
    if not os.path.exists(lg):
        return []
    return [json.loads(l) for l in open(lg) if l.strip()]


def cmd_list():
    if not os.path.isdir(BASE):
        return
    found = False
    for lid in sorted(os.listdir(BASE)):
        _, s, _, _ = paths(lid)
        if not os.path.exists(s):
            continue
        found = True
        st = json.load(open(s))
        opens = sum(1 for p in st.get("prereg", []) if p.get("status") == "open")
        todo = sum(1 for b in st.get("backlog", []) if b.get("status") != "done")
        nx = (st.get("next") or "")[:60]
        print(f"{lid:16} [{st.get('profile','?'):11}] {st.get('dispatch','-'):8} "
              f"cyc={st.get('last',{}).get('cycle','-'):>3}  preg={opens} todo={todo}  next: {nx}")
    if not found:
        print("no loops yet")


def cmd_init(argv):
    if len(argv) < 3:
        sys.exit('usage: loop.py init <id> <profile> "<goal>" [--deadline YYYY-MM-DD]')
    lid, prof, goal = argv[0], argv[1], argv[2]
    deadline = None
    if "--deadline" in argv:
        deadline = argv[argv.index("--deadline") + 1]
    profiles = load_profiles()
    if prof not in profiles:
        sys.exit(f"unknown profile '{prof}'. known: {', '.join(profiles)}")
    p = profiles[prof]
    d, s, lg, _ = paths(lid)
    if os.path.exists(s):
        sys.exit(f"loop '{lid}' already exists")
    os.makedirs(d, exist_ok=True)
    ts = now_iso()
    st = {
        "id": lid, "profile": prof, "goal": goal,
        "created": ts, "updated": ts, "deadline": deadline,
        "dispatch": p.get("dispatch", "schedule"), "cadence": p["cadence"],
        "gate": p["gate"], "triggers": p["triggers"],
        "config": {}, "prereg": [], "backlog": [],
        "last": {"cycle": 0, "ts": ts},
        "next": p["first_directive"],
    }
    save_state(lid, st)
    rec = {"cycle": 0, "ts": ts,
           "observe": {"note": f"spawned [{prof}] loop"},
           "decide": {"verdict": "spawn", "why": f"goal: {goal}"},
           "act": {"change": "loop created from profile"},
           "next": p["first_directive"]}
    with open(lg, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"created loop '{lid}' [{prof}] @ {ts}")
    print(json.dumps(st, indent=2, ensure_ascii=False))


def cmd_state(lid):
    print(json.dumps(load_state(lid), indent=2, ensure_ascii=False))


def cmd_status(lid):
    """Compact one-screen human summary (state.json is the machine view; this is the glance)."""
    st = load_state(lid)
    last = st.get("last", {})
    print(f"{st.get('id')}  [{st.get('profile')}]  dispatch={st.get('dispatch','-')}"
          + (f"  deadline={st['deadline']}" if st.get("deadline") else ""))
    print(f"  goal : {st.get('goal','')}")
    print(f"  gate : {st.get('gate','')}")
    extra = {k: v for k, v in last.items() if k not in ("cycle", "ts")}
    print(f"  last : cycle {last.get('cycle','-')} @ {last.get('ts','-')}" + (f"  {json.dumps(extra, ensure_ascii=False)}" if extra else ""))
    opens = [p for p in st.get("prereg", []) if p.get("status") == "open"]
    for p in opens:
        print(f"  preg {p['id']}: IF {p['trigger']} -> {p['action']}  ({p.get('deadline','-')})")
    todo = [b for b in st.get("backlog", []) if b.get("status") != "done"]
    for b in todo:
        print(f"  todo {b.get('id','?')}: {b.get('want','')}")
    decided = st.get("decided", [])
    if len(decided) > 8:  # keep the glance one-screen; the full ledger lives in state.json
        print(f"  done ({len(decided) - 8} older settled — see `state {st.get('id')}`)")
    for d in decided[-8:]:
        print(f"  done {d.get('key','?')}: {d.get('verdict','')} — {d.get('why','')}")
    for sig, n in author_candidates(st):
        print(f"  AUTHOR-SKILL: '{sig}' hand-rolled {n}x -> /author-skill it (then add to config.skills)")
    print(f"  NEXT : {st.get('next','')}")


def cmd_tail(lid, n=5):
    for r in read_log(lid)[-n:]:
        print(json.dumps(r, ensure_ascii=False))


def cmd_check(lid):
    st = load_state(lid)
    opens = [p for p in st.get("prereg", []) if p.get("status") == "open"]
    if not opens:
        print("no open pre-registrations")
    for p in opens:
        print(f"{p['id']}: IF {p['trigger']} -> {p['action']}  (deadline {p.get('deadline','-')})")
    bl = [b for b in st.get("backlog", []) if b.get("status") != "done"]
    for b in bl:
        print(f"backlog {b.get('id','?')}: {b.get('want','')}  [acceptance: {b.get('acceptance','-')}]")
    for sig, n in author_candidates(st):
        print(f"AUTHOR-SKILL TRIGGER: '{sig}' hand-rolled {n}x (>= {AUTHOR_THRESHOLD}) -> /author-skill it")


DONE_VERDICTS = {"done", "shipped", "verified", "fixed", "pass", "passed", "complete", "confirmed"}
AUTHOR_THRESHOLD = 3  # a hand-rolled step seen this many times -> surface it as an /author-skill trigger


def author_candidates(st):
    """Manual steps recurring enough to freeze into a skill, not yet a registered skill."""
    skills = set(st.get("config", {}).get("skills", []))
    return [(s, n) for s, n in st.get("manual_steps", {}).items()
            if n >= AUTHOR_THRESHOLD and s not in skills]


def cmd_append(lid):
    rec = json.load(sys.stdin)
    for k in ("observe", "decide", "act", "next"):
        if k not in rec:
            sys.exit(f"append: missing required field '{k}'")
    act = rec["act"] if isinstance(rec["act"], dict) else {}

    # FORCED VERIFY GATE: a record that claims work DONE must carry a verify block proving a real check passed.
    # You cannot journal "done" on trust — the helper rejects it. (mark-done = backlog_done, or a done-ish verdict.)
    claims_done = bool(act.get("backlog_done")) or any(
        str(d.get("verdict", "")).strip().lower() in DONE_VERDICTS for d in act.get("decided_add", []))
    if claims_done:
        v = rec.get("verify") or act.get("verify")
        if not isinstance(v, dict) or not v.get("check") or not v.get("result"):
            sys.exit('append REJECTED: this record marks work DONE but has no proof. Add a verify block:\n'
                     '  "verify": {"check": "<the command/test you actually ran>", '
                     '"result": "pass|partial|fail", "evidence": "<output/file:line>"}\n'
                     'Run the real check FIRST, then journal. Done is not a claim — it is a verified fact.')
        if v.get("result") not in ("pass", "partial", "fail"):
            sys.exit('append REJECTED: verify.result must be one of pass|partial|fail')
        if v.get("result") == "fail":
            sys.exit('append REJECTED: verify.result=fail — do not mark work done on a failing check. '
                     'Fix it and re-verify, or record it as not-done (drop backlog_done / use an honest verdict).')

    log = read_log(lid)
    out = {
        "cycle": (log[-1]["cycle"] + 1) if log else 0,
        "ts": now_iso(),
        "observe": rec["observe"], "decide": rec["decide"], "act": rec["act"], "next": rec["next"],
    }
    if rec.get("verify"):
        out["verify"] = rec["verify"]  # keep the proof in the log trail
    _, _, lg, _ = paths(lid)
    with open(lg, "a") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")

    st = load_state(lid)
    st["updated"] = out["ts"]
    st["last"] = {"cycle": out["cycle"], "ts": out["ts"]}
    if isinstance(rec["observe"], dict):
        st["last"].update(rec["observe"])
    st["next"] = rec["next"]
    if rec.get("dispatch"):  # per-tick schedule-vs-loop override (else keep the profile default)
        st["dispatch"] = rec["dispatch"]
    act = rec["act"] if isinstance(rec["act"], dict) else {}
    if act.get("config"):
        st.setdefault("config", {}).update(act["config"])
    for p in act.get("prereg_add", []):
        p.setdefault("status", "open")
        st.setdefault("prereg", []).append(p)
    for pid in act.get("prereg_resolve", []):
        for p in st.get("prereg", []):
            if p.get("id") == pid:
                p["status"] = "resolved"
    for b in act.get("backlog_add", []):
        b.setdefault("status", "open")
        st.setdefault("backlog", []).append(b)
    for bid in act.get("backlog_done", []):
        for b in st.get("backlog", []):
            if b.get("id") == bid:
                b["status"] = "done"
    # decided ledger: compact, durable "what's settled" index (survives rotate; always in state.json).
    # Prevents re-doing/re-exploring work that scrolled past the tail window. One line per settled thing.
    for d in act.get("decided_add", []):
        d.setdefault("cycle", out["cycle"])
        ledger = st.setdefault("decided", [])
        if not any(e.get("key") == d.get("key") for e in ledger):  # dedup by key
            ledger.append(d)
    # AUTHOR-SKILL TRIGGER (mechanical, not vibes): tag a hand-rolled step with act.manual_step (a stable
    # kebab signature = the skill it would become). Count it; status/check surface any sig seen >=AUTHOR_THRESHOLD
    # that isn't yet a config.skill, so a self-evolve pass cannot miss the "freeze this into a skill" signal.
    sig = act.get("manual_step")
    if sig:
        ms = st.setdefault("manual_steps", {})
        ms[sig] = ms.get(sig, 0) + 1
    save_state(lid, st)
    print(f"appended cycle {out['cycle']} @ {out['ts']}; {lid}/state.json updated")


def cmd_rotate(lid, keep=50):
    _, _, lg, arch = paths(lid)
    log = read_log(lid)
    if len(log) <= keep:
        print(f"NOOP ({len(log)} <= keep {keep})")
        return
    old, new = log[:-keep], log[-keep:]
    with open(arch, "a") as f:
        for r in old:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(lg, "w") as f:
        for r in new:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"rotated {len(old)} -> archive; kept {len(new)}")


def cmd_auto(lid, max_iter=12):
    """Arm AI-first autonomous mode: the Stop hook will self-fire /loop-tick <id> until the loop's
    dispatch leaves 'loop', max_iter is hit, or the pointer is removed (loop.py stop)."""
    load_state(lid)  # validates the loop exists
    json.dump({"id": lid, "iteration": 0, "max": int(max_iter)}, open(AUTOLOOP, "w"))
    print(f"armed autonomous loop '{lid}' (max {max_iter} self-fired iterations)")


def cmd_stop():
    if os.path.exists(AUTOLOOP):
        os.remove(AUTOLOOP)
        print("disarmed autonomous loop")
    else:
        print("no autonomous loop armed")


def cmd_autotick():
    """Called by the Stop hook. Decides whether the in-session loop continues. Prints exactly one of:
    'CONTINUE <id>'  -> hook blocks exit and re-feeds /loop-tick <id>
    'STOP <reason>'  -> hook allows exit. Token rail: bounded by max + the tick's own dispatch decision."""
    if not os.path.exists(AUTOLOOP):
        return  # nothing armed -> hook allows normal exit
    a = json.load(open(AUTOLOOP))
    lid, it, mx = a["id"], a["iteration"], a["max"]
    st = load_state(lid)
    dispatch = st.get("dispatch", "")
    if mx > 0 and it >= mx:
        # max bounds the in-session burst, NOT completion. If work remains (the tick still wanted to loop, or
        # the backlog isn't drained), say so loudly — state is fully resumable; the work is paused, not lost.
        work_remains = dispatch == "loop" or any(b.get("status") != "done" for b in st.get("backlog", []))
        os.remove(AUTOLOOP)
        if work_remains:
            print(f"STOP {lid} max-iterations ({mx}) INCOMPLETE: work remains — resume from state.next via "
                  f"`loop.py auto {lid}` (new burst) or a cron firing /loop-tick {lid}. Nothing lost; state is resumable.")
        else:
            print(f"STOP {lid} max-iterations ({mx}) complete")
        return
    if dispatch != "loop":
        os.remove(AUTOLOOP); print(f"STOP dispatch={dispatch} (loop chose to wait)"); return
    a["iteration"] = it + 1
    json.dump(a, open(AUTOLOOP, "w"))
    print(f"CONTINUE {lid}")


def cmd_rm(lid):
    d, s, _, _ = paths(lid)
    if not os.path.exists(s):
        sys.exit(f"no loop '{lid}'")
    shutil.rmtree(d)
    print(f"removed loop '{lid}'")


def need_id(a, cmd):
    if len(a) < 2:
        sys.exit(f"usage: loop.py {cmd} <id>")
    return a[1]


def opt_int(a, i, default, cmd, name):
    if len(a) <= i:
        return default
    try:
        return int(a[i])
    except ValueError:
        sys.exit(f"usage: loop.py {cmd} <id> [{name}]  ({name} must be an integer, got {a[i]!r})")


def main():
    a = sys.argv[1:] or ["list"]
    cmd = a[0]
    if cmd == "list":
        cmd_list()
    elif cmd == "init":
        cmd_init(a[1:])
    elif cmd == "state":
        cmd_state(need_id(a, cmd))
    elif cmd == "status":
        cmd_status(need_id(a, cmd))
    elif cmd == "tail":
        cmd_tail(need_id(a, cmd), opt_int(a, 2, 5, cmd, "N"))
    elif cmd == "check":
        cmd_check(need_id(a, cmd))
    elif cmd == "append":
        cmd_append(need_id(a, cmd))
    elif cmd == "rotate":
        cmd_rotate(need_id(a, cmd), opt_int(a, 2, 50, cmd, "KEEP"))
    elif cmd == "rm":
        cmd_rm(need_id(a, cmd))
    elif cmd == "auto":
        cmd_auto(need_id(a, cmd), opt_int(a, 2, 12, cmd, "MAX"))
    elif cmd == "stop":
        cmd_stop()
    elif cmd == "autotick":
        cmd_autotick()
    else:
        sys.exit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()
