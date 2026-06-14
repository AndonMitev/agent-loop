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
  state <id>                        print state.json — what a tick reads FIRST.
  tail <id> [N]                     last N log records (default 5) — context for a tick.
  check <id>                        list OPEN pre-registrations + deadlines.
  append <id>                       read one JSON record from stdin, stamp cycle+ts, append, update state.
                                      stdin schema: {"observe":{...},"decide":{...},"act":{...},"next":"..."}
                                      optional in "act": "config":{...}        -> merge into state.config
                                                         "prereg_add":[{id,trigger,action,deadline}]
                                                         "prereg_resolve":["P1"]
                                                         "backlog_add":[{id,want,acceptance}]
                                                         "backlog_done":["B1"]
  rotate <id> [KEEP]                fold all but the last KEEP records to log.archive.jsonl (default 50).
"""
import json, os, sys, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
PROFILES = os.path.join(BASE, "profiles.json")


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
        nx = (st.get("next") or "")[:70]
        print(f"{lid:16} [{st.get('profile','?'):11}] cyc={st.get('last',{}).get('cycle','-'):>3}  preg={opens}  next: {nx}")
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


def cmd_append(lid):
    rec = json.load(sys.stdin)
    for k in ("observe", "decide", "act", "next"):
        if k not in rec:
            sys.exit(f"append: missing required field '{k}'")
    log = read_log(lid)
    out = {
        "cycle": (log[-1]["cycle"] + 1) if log else 0,
        "ts": now_iso(),
        "observe": rec["observe"], "decide": rec["decide"], "act": rec["act"], "next": rec["next"],
    }
    _, _, lg, _ = paths(lid)
    with open(lg, "a") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")

    st = load_state(lid)
    st["updated"] = out["ts"]
    st["last"] = {"cycle": out["cycle"], "ts": out["ts"]}
    if isinstance(rec["observe"], dict):
        st["last"].update(rec["observe"])
    st["next"] = rec["next"]
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


def main():
    a = sys.argv[1:] or ["list"]
    cmd = a[0]
    if cmd == "list":
        cmd_list()
    elif cmd == "init":
        cmd_init(a[1:])
    elif cmd == "state":
        cmd_state(a[1])
    elif cmd == "tail":
        cmd_tail(a[1], int(a[2]) if len(a) > 2 else 5)
    elif cmd == "check":
        cmd_check(a[1])
    elif cmd == "append":
        cmd_append(a[1])
    elif cmd == "rotate":
        cmd_rotate(a[1], int(a[2]) if len(a) > 2 else 50)
    else:
        sys.exit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()
