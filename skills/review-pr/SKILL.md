---
name: review-pr
description: Review a pull request. Detects GitHub or Bitbucket, pulls ticket context from Jira or Linear, fans reviewer agents out over the diff, verifies their findings against the PR head, then posts inline comments and a verdict. Use when asked to review a specific PR or when a PR link is shared for review. It posts to the PR, so run it only for a real review of a real PR, never as background analysis.
argument-hint: "[PR | TICKET-KEY | URL] [--repo owner/repo] [--local] [--no-approve] [correctness|errors|tests|quality|all]"
allowed-tools: ["Bash", "Read", "Grep", "Glob", "Agent"]
---

Arguments: "$ARGUMENTS"

References live in `~/.claude/review/`: `hosts.md` (GitHub and Bitbucket calls), `tickets.md` (Jira and Linear), `verification.md` (the evidence discipline, including the `(unverified)` contract), `diagnosis.md` (judging a claimed defect cause), `decision-authority.md` (what you decide versus what you escalate). Read a reference at the step that needs it, not upfront.

Two rules govern the whole run.

**The diff never enters your context.** It goes to disk and the agents read it there. You only ever see derived metadata: `wc -l`, the changed-file list, grep counts. Do not cat it, capture it in a variable, or re-emit it when writing files.

**You are adversarial by default.** Agent findings are claims, not results. Nothing gets posted until you have checked it, and nothing gets approved because nobody objected.

## 1. Resolve the target

PR number, a ticket key (`[A-Z][A-Z0-9]+-[0-9]+`), a PR URL, or nothing (detect from the current branch). `--repo` overrides the repo; see hosts.md for parsing and for which host a bare `owner/repo` means. Flags: `--local` (show, do not post), `--no-approve` (never post an approve event, whatever the verdict). Aspects default to all.

Given a ticket key, list open PRs and match its lowercase form against title and branch name. Linear branches are lowercase, so a case-sensitive match reports "no open PR" on a PR that exists. No match means ask the user rather than guessing.

## 2. Set up

```bash
DIR=$(mktemp -d /tmp/pr-review-XXXXXX); DIFF="$DIR/diff.patch"
```
Fetch PR metadata (small, fine to hold) and the diff straight to disk, per hosts.md. Then:
```bash
DIFF_LINES=$(wc -l < "$DIFF"); CHANGED=$(grep '^diff --git' "$DIFF" | sed 's|.* b/||')
```

## 3. Put the PR head on disk

Every "check it against the source" instruction below depends on this. Without it a grep runs against whatever is checked out, usually the base branch, and under `--repo` an unrelated repository. All three failure modes return a plausible answer, so a fabricated finding is indistinguishable from a verified one.

```bash
TREE=""; TREE_REV=""
if [ -z "$REPO_OVERRIDE" ] && git rev-parse --git-dir >/dev/null 2>&1 \
   && git fetch -q --force origin "refs/pull/$PR/head:refs/remotes/origin/pr/$PR"; then
  TREE_REV=$(git rev-parse "refs/remotes/origin/pr/$PR")
  git worktree add -q --detach "$DIR/head" "$TREE_REV" && TREE="$DIR/head"
fi
```
Bitbucket has no `refs/pull/N/head`; fetch the source branch by name instead. Confirm `TREE_REV` equals the head SHA from the PR object before using the tree. If it does not match, or the fetch failed, there is no tree.

Tell the agents which case holds, explicitly. With a tree: this path is the PR head, greps and reads against it are authoritative. Without one: say so in those words, tell them not to grep the working directory because it is a different commit, and tell them any claim needing source must be labelled `(unverified)` or raised as an open question.

## 4. Read what is already on the PR

Fetch inline comments, general comments and reviews (hosts.md). **Check the fetch.** An expired token returns an error body that parses as "no comments", and the logic below suppresses findings based on this data, so a failed fetch and a quiet PR become the same state and the failure direction drops findings silently. On failure or an unexpected shape, set `COMMENTS_UNAVAILABLE`, skip all suppression, report every finding, and say so in the summary.

Classify what comes back.

A previous review by this skill (body contains `Reviewed by /review-pr`) makes this a re-review: take its timestamp, fetch commits since, diff that range to `$DIR/incremental.patch`, and make the incremental diff the primary target with the full diff still on disk for context.

Comments by the PR author are a self-review checklist, not reviewer feedback. Authors often find things and then fix them in later commits. Map each self-finding to the commit that followed it, or mark it still open; if the commit list is unavailable, pass them through as open rather than guessing at a resolution. Brief the agents to check whether those fixes actually landed, what the author missed, and what they acknowledged but chose not to fix. An acknowledgement does not downgrade severity: "aware this swallows the error, leaving it" is a known critical, not a handled one. Otherwise an author silences any finding by conceding it first.

Comments by other reviewers: report only what they have not already raised. If your finding matches one, add the specific thing that extends it (a correction, a measurement, a reachability detail) and say you are adding to their thread. If you have nothing to add, drop it. Never drop a critical silently: state it as a one-line confirmation of their point. Match on the defect, not the file; two comments on one file are not the same finding, and a match against a resolved thread is not a match. Record what you suppressed and against which thread, because "found no criticals" and "found three and swallowed them as near-matches" otherwise read identically.

## 5. Ticket context

Follow `~/.claude/review/tickets.md`: extract a candidate, resolve which provider owns it, fetch, normalise. A candidate no provider claims is discarded and the review proceeds without ticket context. Never put an unconfirmed candidate in the summary.
Unreachable and not-found are different claims. An auth failure reported as a missing ticket is how a PR with acceptance criteria gets reviewed as though it had none.

## 6. Assemble the context file

Write the small header as a heredoc, then `cat` the diff onto it, in one Bash call:

```bash
cat > "$DIR/header.md" <<'HDR'
# Review context
## PR
title / author / branch -> base / url / head SHA / mode (first review | re-review, N commits since DATE)
## Tree
PR head checked out at {TREE} ({TREE_REV}) -- authoritative   |   NO TREE: do not grep the working directory
## Ticket
provider / key / url / summary / status / priority / description and acceptance criteria / sub-issues
## Existing comments
unresolved inline, then general, then author self-review with its mapped fix commits
## Diff
HDR
cat "$DIR/header.md" "${TARGET_DIFF}" > "$DIR/context.md"
```
On a re-review, `TARGET_DIFF` is the incremental patch and you append a line pointing at `$DIFF` for broader context. Never write diff content yourself; only `cat` moves it.

## 7. Fan out

Gate agents with cheap greps over the target diff. Each skipped agent saves a spawn.

```bash
SOURCE=$(grep '^diff --git' "$T" | grep -cvE '\.(md|txt|json|ya?ml|lock)$' || true)
QUALITY=$(grep -cE '^\+\s*(//|/\*|\*|#)|^\+.*\b(interface|type|class|enum|struct)\b' "$T" || true)
```

| Aspect | Agent | Run when |
|---|---|---|
| correctness | `review-correctness` | always |
| errors | `review-failure-modes` | always |
| tests | `review-tests` | `SOURCE > 0` |
| quality | `review-maintainability` | `QUALITY > 0` |

Launch them in one message so they run concurrently. Each prompt carries: the context file path, the tree path or the explicit no-tree statement, the ticket provider and key if any, the reference directory as an absolute path (`REF=$(cd ~/.claude/review && pwd)`, since a subagent's Read will not expand `~`), and this instruction:

```
Report findings as file:line using NEW-FILE line numbers from the right side of the diff.
Derive them from the @@ hunk headers. A finding you cannot anchor is still worth
reporting; say so rather than inventing a line.
```
On a re-review add: focus on the incremental diff, check whether unresolved human comments are addressed, verify previously missing requirements, and do not repeat prior findings unless they survive in the new code.

## 8. Verify before you believe any of it

This is the step that makes the review worth posting. Read `~/.claude/review/verification.md` and apply it to the agents' output.

Resolve every conditional finding. "If X is set, then", "depends on whether the consumer does Y", "the author should confirm" means the agent lacked one fact and your job is to supply it. Spend a tool call or two: grep where the flag is set, read the consuming file, read the deployment source of truth rather than a README describing it. Then either promote it to a concrete finding with the resolved fact and `file:line`, or raise it as an explicit open question. Never pass the hedge through.

A finding carrying `(unverified)` is a conditional finding and goes through the same step. Resolve each against the tree. Anything still unverified afterwards is demoted below critical and states what could not be checked and why. Count them; the summary carries the number, so a reader can see how much of the verdict rests on unchecked claims.

Spot-check the load-bearing findings against source, most cheaply by reading the context around any finding resting on a single grep hit: a comment quoting its own former error matches a search for that error. Check suggested fixes separately from the diagnoses they arrive with (V5). Before citing a clean result or a green gate as coverage, establish that it could have failed (V9).

Deduplicate across agents and against the existing comments from step 4.

## 9. Verdict

Decide it yourself, from what survived step 8, and default to refusing. Nobody objecting is not evidence.

- **REQUEST_CHANGES**: any critical survives.
- **COMMENT**: no critical, but importants survive, or unverified findings remain, or `COMMENTS_UNAVAILABLE`, or you could not confirm the head is current.
- **APPROVE**: nothing above critical or important survived, the head is confirmed current, requirement coverage is complete except for author-side validation criteria, and you have a tree. Suggestions alone do not block.

`--no-approve` caps the verdict at COMMENT. `--local` posts nothing.
The poster enforces the approve floor mechanically and has no override, so a verdict you cannot defend will simply be refused rather than argued with.

An acceptance criterion describing how the author validates their own work is never a blocker: list it outstanding and judge the change on the code findings.

Read `~/.claude/review/decision-authority.md` before the verdict. It owns the line between a finding you settle and one you put to a human, and the five elements an escalation has to carry. Two of its rules bind you here: a reviewer's wording never amends the accepted contract, and repeated findings on one theme are themselves the finding, not four independent ones to fix.

## 10. Re-check the head, then post

A PR you started reviewing minutes ago may have moved, and inline comments anchor to the diff of the current head. Resolve the head from the PR object plus a forced ref fetch, never a cached summary field, which serves stale SHAs. Re-read comments too, so you do not post a finding someone raised while you were working.
If the head moved, redo step 2 rather than posting against the old diff. If no fetch path works, stop and report. This is a hard gate; the graceful-degradation posture everywhere else does not cover it (V6).

Write `$DIR/findings.json` (`{"summary": "...", "findings": [{"file", "line", "body", "severity"}]}`, severity being `critical`, `important` or `suggestion`) and post:

```bash
python3 ~/.claude/review/post-review.py --host "$HOST" --owner "$OWNER" --repo "$REPO" \
  --pr "$PR" --findings "$DIR/findings.json" --diff "$DIFF" --event "$VERDICT" --head "$TREE_REV"
```
It resolves anchors against the on-disk diff and downgrades anything it cannot anchor to a general comment, so resolve anchors there rather than pulling hunks into your context. It also re-reads the head itself and exits non-zero if the PR moved or the head cannot be read, and refuses an APPROVE carrying a critical, an important, or an `(unverified)` finding. Both refusals are the gate working; do not route around either.

Summary shape:

```markdown
## Review: {title}
**Ticket:** [KEY](url) - summary (Provider, Status)
**Scope:** first review | N commits since {date}

### Requirement coverage
- [x] AC1 ... - implemented at file:line
- [ ] AC2 ... - not found in diff

### Findings
Critical N | Important N | Suggestions N | Unverified N | Already raised by others N

### Verdict
{one paragraph, then the decision and what would change it}

---
*Reviewed by /review-pr*
```

## 11. Clean up and report

`git worktree remove --force "$DIR/head" 2>/dev/null; rm -rf "$DIR"`

Report: host, mode, ticket key and which provider claimed it or that none did, agents run, finding counts, verdict, posted or local, and the full canonical PR URL. Say what you could not do and why, every time. State a verdict you could not reach honestly as exactly that.

## Running under /team

The lead invokes this skill; the reviewer agents are its fan-out, not team members. That boundary is deliberate: durable work that has to survive a restart goes into a herdr pane with its own state, while an ephemeral read-only analysis the lead consumes in the same turn goes to a subagent. Spawning durable work as a subagent produces work herdr cannot see and the lead cannot recover. Map the verdict onto the team protocol: APPROVE becomes `PASS <pr-url> <verdict line>`, REQUEST_CHANGES and COMMENT become `FAIL <pr-url> <critical and important findings>` back to the engineer. A verdict you could not reach is `BLOCKED <reason>` to the human, never an approve.
