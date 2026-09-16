#!/usr/bin/env python3
"""Post a review to GitHub or Bitbucket: inline comments anchored against the
on-disk diff, plus a summary, in one pass.

findings.json: {"summary": "markdown", "findings": [
  {"file": ..., "line": ..., "body": ..., "severity": "critical|important|suggestion"}]}
A finding whose line is not on the new-file side of the diff is downgraded to a
general comment carrying file:line in its text, never posted as an unanchored
inline comment (which lands silently at the top of the file).

Two gates are mechanical here rather than left to the caller, because both fail
silently when a long run forgets them:

- the head this review was built against must still be the PR's head (V6), and
- APPROVE is refused while any critical or important finding, or any finding
  still carrying the (unverified) token, is being posted (V1, V5).

Neither has an override flag. An unresolvable head is a stop, not a warning.
"""
import argparse
import json
import os
import re
import subprocess
import sys


def commentable_lines(diff_path):
    """file -> set of new-file line numbers that can carry an inline comment."""
    lines = {}
    current, new_line = None, None
    with open(diff_path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            if raw.startswith("diff --git"):
                m = re.search(r" b/(.+?)\s*$", raw)
                current = m.group(1) if m else None
                new_line = None
            elif raw.startswith("@@"):
                m = re.search(r"\+(\d+)", raw)
                new_line = int(m.group(1)) if m else None
            elif current and new_line is not None:
                if raw.startswith("+") or raw.startswith(" "):
                    lines.setdefault(current, set()).add(new_line)
                    new_line += 1
                elif raw.startswith(("-", "\\")):
                    pass
                else:
                    new_line += 1
    return lines


BLOCKING = {"critical", "important"}


def approve_blockers(findings):
    """Reasons this finding set forbids an APPROVE event."""
    reasons = []
    blocking = [f for f in findings if str(f.get("severity", "")).lower() in BLOCKING]
    if blocking:
        reasons.append(f"{len(blocking)} critical/important finding(s): "
                       + ", ".join(f"{f.get('file')}:{f.get('line')}" for f in blocking[:5]))
    unverified = [f for f in findings if "(unverified)" in f.get("body", "")]
    if unverified:
        reasons.append(f"{len(unverified)} finding(s) still marked (unverified)")
    return reasons


def current_head(host, owner, repo, pr):
    """The PR's head SHA read from the host now. Raises if it cannot be read."""
    if host == "github":
        out = gh([f"repos/{owner}/{repo}/pulls/{pr}", "--jq", ".head.sha"]).strip()
    else:
        out = json.loads(bb("GET", f"https://api.bitbucket.org/2.0/repositories/"
                                   f"{owner}/{repo}/pullrequests/{pr}"))
        out = (out.get("source") or {}).get("commit", {}).get("hash", "")
    if not out:
        raise SystemExit("could not read the PR head; refusing to post (see verification.md V6)")
    return out


def same_commit(a, b):
    """Bitbucket serves abbreviated hashes, so compare on the shorter prefix."""
    a, b = a.strip().lower(), b.strip().lower()
    n = min(len(a), len(b))
    return n >= 7 and a[:n] == b[:n]


def split(findings, anchors):
    inline, general = [], []
    for f in findings:
        path, line = f.get("file"), f.get("line")
        if path and line and line in anchors.get(path, set()):
            inline.append({"path": path, "line": int(line), "side": "RIGHT", "body": f["body"]})
        else:
            where = f"`{path}:{line}`" if path else ""
            general.append(f"{where} {f['body']}".strip())
    return inline, general


def gh(args, payload=None):
    proc = subprocess.run(
        ["gh", "api"] + args + (["--input", "-"] if payload is not None else []),
        input=json.dumps(payload) if payload is not None else None,
        text=True, capture_output=True,
    )
    if proc.returncode:
        sys.exit(f"gh api failed: {proc.stderr.strip()}")
    return proc.stdout


def bb(method, url, payload=None):
    cmd = ["curl", "-fsS", "-u", f"{os.environ['BB_EMAIL']}:{os.environ['BITBUCKET_TOKEN']}",
           "-X", method, url]
    if payload is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(payload)]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode:
        sys.exit(f"bitbucket {method} {url} failed: {proc.stderr.strip()}")
    return proc.stdout


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", choices=["github", "bitbucket"], required=True)
    p.add_argument("--owner", required=True, help="GitHub owner or Bitbucket workspace")
    p.add_argument("--repo", required=True)
    p.add_argument("--pr", required=True)
    p.add_argument("--findings", required=True)
    p.add_argument("--diff", required=True)
    p.add_argument("--event", default="COMMENT",
                   choices=["COMMENT", "APPROVE", "REQUEST_CHANGES"])
    p.add_argument("--head", required=True,
                   help="head SHA this review was built against; posting is refused if it moved")
    a = p.parse_args()

    data = json.load(open(a.findings, encoding="utf-8"))
    findings = data.get("findings", [])

    if a.event == "APPROVE":
        blockers = approve_blockers(findings)
        if blockers:
            sys.exit("refusing APPROVE: " + "; ".join(blockers))

    live = current_head(a.host, a.owner, a.repo, a.pr)
    if not same_commit(live, a.head):
        sys.exit(f"head moved: reviewed {a.head}, PR is now at {live}. "
                 "Re-run the review against the current head; do not post this one.")

    inline, general = split(findings, commentable_lines(a.diff))
    summary = data.get("summary", "")
    if general:
        summary += "\n\n### Findings without a diff anchor\n" + "\n\n".join(f"- {g}" for g in general)

    if a.host == "github":
        gh([f"repos/{a.owner}/{a.repo}/pulls/{a.pr}/reviews", "--method", "POST"],
           {"body": summary, "event": a.event, "comments": inline})
    else:
        base = f"https://api.bitbucket.org/2.0/repositories/{a.owner}/{a.repo}/pullrequests/{a.pr}"
        for c in inline:
            bb("POST", f"{base}/comments",
               {"content": {"raw": c["body"]}, "inline": {"path": c["path"], "to": c["line"]}})
        bb("POST", f"{base}/comments", {"content": {"raw": summary}})
        if a.event == "APPROVE":
            bb("POST", f"{base}/approve")

    print(f"posted {len(inline)} inline, {len(general)} unanchored, 1 summary, "
          f"event={a.event}, head={live}")


if __name__ == "__main__":
    main()
