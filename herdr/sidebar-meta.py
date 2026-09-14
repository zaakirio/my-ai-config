#!/usr/bin/env python3
"""Report tab/pane counts, ages, and git badges into the Herdr sidebar as custom tokens.

Spaces get $tabs, $panes, $since (date the space was first seen), $age (relative
age), and $git (dirty count / ahead / behind for the space's repo).
Agent panes get $since, $age (time the agent session was first seen), and
$elapsed (how long the agent has been in the working state; cleared otherwise).
Runs forever; kept alive by launchd (dev.herdr.sidebar-meta).
"""
import json
import os
import socket
import subprocess
import sys
import threading
import time
from collections import Counter
from datetime import datetime

CONFIG_DIR = os.path.expanduser("~/.config/herdr")
SOCKET = os.path.join(CONFIG_DIR, "herdr.sock")
STATE_FILE = os.path.join(CONFIG_DIR, "sidebar-meta-state.json")
SOURCE = "sidebar-meta"
TTL_MS = 180_000
REFRESH_S = 60
DEBOUNCE_S = 0.3
GIT_REFRESH_S = 60
GIT_TIMEOUT_S = 10
SUBSCRIPTIONS = [
    "workspace.created", "workspace.closed", "workspace.renamed",
    "tab.created", "tab.closed",
    "pane.created", "pane.closed", "pane.exited", "pane.agent_detected",
    "pane.agent_status_changed",
    "layout.updated",
]


def log(msg):
    sys.stderr.write(f"{datetime.now():%Y-%m-%dT%H:%M:%S} {msg}\n")
    sys.stderr.flush()


def load_state():
    try:
        with open(STATE_FILE) as f:
            s = json.load(f)
        s.setdefault("workspaces", {})
        s.setdefault("agents", {})
        s.setdefault("working", {})
        return s
    except Exception:
        return {"workspaces": {}, "agents": {}, "working": {}}


def save_state(state):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_FILE)


def rpc(method, params):
    c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    c.settimeout(5)
    c.connect(SOCKET)
    c.sendall((json.dumps({"id": "sm", "method": method, "params": params}) + "\n").encode())
    buf = b""
    while b"\n" not in buf:
        d = c.recv(1 << 16)
        if not d:
            break
        buf += d
    c.close()
    resp = json.loads(buf.split(b"\n")[0])
    if "error" in resp:
        raise RuntimeError(f"{method}: {resp['error']}")
    return resp.get("result")


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def fmt_date(ts):
    return datetime.fromtimestamp(ts).strftime("%-d %b")


def fmt_when(ts):
    d = datetime.fromtimestamp(ts)
    if d.date() == datetime.now().date():
        return d.strftime("%H:%M")
    return d.strftime("%-d %b %H:%M")


def fmt_dur(seconds):
    m = int(seconds // 60)
    if m < 1:
        return "<1m"
    if m < 60:
        return f"{m}m"
    h = m // 60
    if h < 24:
        rem = m % 60
        return f"{h}h{rem}m" if rem and h < 4 else f"{h}h"
    d = h // 24
    if d < 30:
        return f"{d}d"
    return f"{d // 7}w"


def fmt_age(ts):
    return fmt_dur(time.time() - ts)


def workspace_cwds(snap):
    """Most-common pane cwd per workspace (foreground_cwd preferred)."""
    by_ws = {}
    for pane in snap["panes"]:
        cwd = pane.get("foreground_cwd") or pane.get("cwd")
        if cwd:
            by_ws.setdefault(pane["workspace_id"], []).append(cwd)
    out = {}
    for wid, cwds in by_ws.items():
        out[wid] = Counter(cwds).most_common(1)[0][0]
    return out


GIT_ENV = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}


def git_badge(cwd):
    """Dirty count and ahead/behind for cwd, e.g. '●3 ↑1'. None when clean or not a repo."""
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "status", "--porcelain=v1", "--branch"],
            capture_output=True, text=True, timeout=GIT_TIMEOUT_S, env=GIT_ENV,
        )
    except Exception:
        return None
    if r.returncode != 0 or not r.stdout:
        return None
    lines = r.stdout.splitlines()
    dirty = sum(1 for ln in lines if not ln.startswith("## "))
    ahead = behind = 0
    if lines and "[" in lines[0]:
        bracket = lines[0].split("[", 1)[1].rstrip("]")
        for part in bracket.split(", "):
            if part.startswith("ahead "):
                ahead = int(part[6:])
            elif part.startswith("behind "):
                behind = int(part[7:])
    parts = []
    if dirty:
        parts.append(f"●{dirty}")
    if ahead:
        parts.append(f"↑{ahead}")
    if behind:
        parts.append(f"↓{behind}")
    return " ".join(parts) if parts else None


def report(state, git_cache):
    snap = rpc("session.snapshot", {})["snapshot"]
    now = time.time()
    seq = time.time_ns()
    dirty = False

    cwds = workspace_cwds(snap)

    live_ws = set()
    for ws in snap["workspaces"]:
        wid = ws["workspace_id"]
        live_ws.add(wid)
        if wid not in state["workspaces"]:
            state["workspaces"][wid] = now
            dirty = True
        cwd = cwds.get(wid)
        if cwd and now - git_cache.get(wid, (0,))[0] >= GIT_REFRESH_S:
            git_cache[wid] = (now, git_badge(cwd))
        badge = git_cache.get(wid, (0, None))[1]
        rpc("workspace.report_metadata", {
            "workspace_id": wid,
            "source": SOURCE,
            "seq": seq,
            "ttl_ms": TTL_MS,
            "tokens": {
                "tabs": plural(ws["tab_count"], "tab"),
                "panes": plural(ws["pane_count"], "pane"),
                "since": fmt_date(state["workspaces"][wid]),
                "age": fmt_age(state["workspaces"][wid]),
                "git": badge,
            },
        })

    live_agents = set()
    for pane in snap["panes"]:
        if not pane.get("agent"):
            continue
        sess = pane.get("agent_session") or {}
        key = f"{pane['pane_id']}|{sess.get('value', '')}"
        live_agents.add(key)
        if key not in state["agents"]:
            state["agents"][key] = now
            dirty = True
        tokens = {
            "since": fmt_when(state["agents"][key]),
            "age": fmt_age(state["agents"][key]),
        }
        if pane.get("agent_status") == "working":
            if key not in state["working"]:
                state["working"][key] = now
                dirty = True
            tokens["elapsed"] = fmt_dur(now - state["working"][key])
        else:
            if key in state["working"]:
                del state["working"][key]
                dirty = True
            tokens["elapsed"] = None
        rpc("pane.report_metadata", {
            "pane_id": pane["pane_id"],
            "source": SOURCE,
            "seq": seq,
            "ttl_ms": TTL_MS,
            "tokens": tokens,
        })

    # Prune entries for spaces/agents that no longer exist so the file stays small.
    for k in [k for k in state["workspaces"] if k not in live_ws]:
        del state["workspaces"][k]
        git_cache.pop(k, None)
        dirty = True
    for k in [k for k in state["agents"] if k not in live_agents]:
        del state["agents"][k]
        dirty = True
    for k in [k for k in state["working"] if k not in live_agents]:
        del state["working"][k]
        dirty = True
    if dirty:
        save_state(state)


def event_listener(wake):
    """Nudge the main loop whenever the session shape changes."""
    while True:
        try:
            c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            c.connect(SOCKET)
            subs = [{"type": t} for t in SUBSCRIPTIONS]
            c.sendall((json.dumps({"id": "ev", "method": "events.subscribe",
                                   "params": {"subscriptions": subs}}) + "\n").encode())
            while True:
                d = c.recv(1 << 16)
                if not d:
                    break
                wake.set()
        except Exception as e:
            log(f"event stream down: {e}")
        time.sleep(3)


def main():
    state = load_state()
    git_cache = {}
    wake = threading.Event()
    threading.Thread(target=event_listener, args=(wake,), daemon=True).start()
    while True:
        # Clear before reporting so an event that lands mid-report is not lost.
        wake.clear()
        try:
            report(state, git_cache)
        except Exception as e:
            log(f"report failed: {e}")
        if wake.wait(REFRESH_S):
            time.sleep(DEBOUNCE_S)


if __name__ == "__main__":
    main()
