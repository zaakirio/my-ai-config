---
name: zk-fix
description: Apply review feedback on a pull request. Fetches the comments, separates what is actionable from what needs a human, applies the fixes, and replies to every finding with what happened. Use when explicitly asked to address or fix review feedback on a specific PR. Edits the working tree; it only commits, pushes or replies when those flags are passed.
argument-hint: "[PR] [--repo owner/repo] [--dry-run] [--commit] [--push] [--reply] [--from all|bot|humans]"
allowed-tools: ["Bash", "Read", "Edit", "Grep", "Glob"]
---

Arguments: "$ARGUMENTS"

References in `~/.claude/review/`: `hosts.md` for the host calls, `response-shapes.md` for replies, `verification.md` for the evidence discipline, `decision-authority.md` for what you settle versus what goes to a human, `diagnosis.md` when a finding rests on a claimed cause. Read each at the step that needs it.

Default is edit and stop. `--commit`, `--push`, `--reply` are opt-in and additive; `--push` implies `--commit`, `--reply` requires it.

## 1. Resolve and check out

PR number, or detect from the current branch. Detect the host from the remote or `--repo` (hosts.md).
Compare the PR source branch to the local branch and warn on a mismatch without aborting; worktrees and detached HEAD are valid. Warn on a dirty tree too, and stop if it would collide with the files you are about to edit.

## 2. Fetch and classify the comments

Fetch inline comments, general comments and reviews with pagination (hosts.md). Check the calls succeeded; an error body parses as "no comments" and you would report a clean run having done nothing.

Drop: deleted comments, resolved threads, roll-up summaries, and replies (anything with a parent), which are responses to findings rather than findings.
`--from` filters by author: `bot` keeps automated review comments, `humans` keeps the rest, `all` is the default.

Split what remains into actionable and needs-human. Needs-human is a genuine question, praise, a product decision ("should we", "do we want"), meta-discussion, or a status update. Everything else is actionable. When unsure, call it needs-human: skipping a fixable comment is cheaper than making someone else's product decision.

## 3. Present, then stop if asked

Group by file, show line, author and the comment, then the needs-human list and any general comments. On `--dry-run`, stop here.

## 4. Apply

Write the findings to `$(mktemp -d)/fixes.md` so you are not re-reading the API payload, then work file by file, **highest line number first**, so earlier edits do not shift later anchors.

Per finding:
1. Fix only what the comment asks for. No adjacent refactoring, no drive-by improvements, no expanding on the idea.
2. The finding and the fix suggested with it are two claims. A reviewer sees the diff, not the runtime, so correct diagnosis with a wrong prescription is the common case. Check the prescription against the tree before applying it; if the finding holds but their fix does not, fix it correctly and say so in the reply (verification.md V5).
3. A factual claim you adopt from a reviewer becomes yours the moment you write it into code, a comment or a response. It needs the same evidence as one you authored (V10).
4. If the fix is a class of problem rather than one site, grep for siblings and either fix them here or record the deferral explicitly (V2).
5. A finding resting on a claimed cause is only as good as that cause. Read `~/.claude/review/diagnosis.md` before implementing one: fixing the masking condition makes the symptom go away and leaves the defect.
6. Ambiguous or product-shaped, skip it and record why. `~/.claude/review/decision-authority.md` draws the line, and you do not adjudicate a finding against your own change: apply the decision or escalate it, never decide it.

After each file, run whatever the project actually gates on: typecheck, lint, the relevant tests. If validation fails, revert that file (`git checkout -- <file>`) and record it as reverted with the error. Do not leave a half-applied file behind.

Track every finding as fixed, skipped or reverted.

## 5. Show the work

`git diff`, then counts of fixed, skipped and reverted, each skipped and reverted item named with its reason. Without `--commit` or `--push`, stop here.

## 6. Commit

Stage only the files you changed, never `git add -A`.

```
fix(review): address PR #N review findings

Fixed K findings. Skipped L (ambiguous or needs a human).
```
Then capture the short SHA.

## 7. Re-check before pushing or replying

Re-fetch comments and reviews newer than your step 2 fetch. Reviews arrive in bursts and a fetch taken at the start of the cycle is stale by the time the fix is ready. If anything new arrived, present it and stop for the user's call; it may change what the commit should contain. If the re-check itself fails, report and stop rather than pushing against an unknown state (V6).

## 8. Push

`git push`. Never force-push. Anything new lands as an additional commit, never an amend of something already pushed. If the push fails, report it and stop.

## 9. Reply

Every classified finding gets a reply, including the ones you did not action. Silence is not an outcome. Use the four shapes in `~/.claude/review/response-shapes.md`:

| outcome | shape |
|---|---|
| fixed | **Fixed in `sha`** plus what changed and why |
| skipped as out of scope, or partially fixed | **Deferred** with where it is tracked, and the partial commit if there is one |
| skipped as a product decision, or the finding does not hold | **Disputed** with the technical reason and what would change your mind |
| reverted, or classified needs-human | **Investigated** with what you checked and what you found |

A bare `Fixed in abc1234` is not a reply. Never claim Fixed without confirming the commit actually addresses the finding; a partial fix is Deferred.
Post replies as children of the original comment (hosts.md), half a second apart.

## 10. Report

Host, PR title and canonical URL, counts by outcome, the commit if any, whether it was pushed, how many replies were posted, and anything you could not do. Remove the temp directory.

## Running under /team

The engineer runs this against the lead's FAIL. Report `DONE <branch> <fixed/skipped/reverted counts + sha>` to the lead and `REVIEW <branch> <what changed>` to QA. Findings you disputed go to the lead as part of DONE, not silently dropped: the lead decides whether the dispute stands.
