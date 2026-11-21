---
name: zk-handover
description: Pause or wrap up work so another agent can resume it cold, or resume from such a handover. Use for "handover doc", "hand this over", "wrap up", "pause", "I'm closing this", "before my instance dies", or "continue where the last agent left off". Not for status reports; use the status workflow for those.
---

## Pause or wrap up

Stop at a safe boundary: finish or back out of the current atomic step, start nothing new, and stop any workers you started.
Make the work durable: commit uncommitted edits as one `wip:` commit on the current branch, through `pr-owner run` when the branch is claimed; say in the commit body if the tree is broken.
Push only when the branch already has a PR or the user asked; a pause takes no other irreversible action.
Release your `pr-owner` claim unless this session keeps writing the branch.
Write the note to a file outside the repo, default `~/Development/handovers/<repo>-<branch-or-topic>.md`, and give its path.

The note holds, in this order:
1. Goal and the accepted behavior, in the user's terms.
2. Exact state: repo path, worktree, branch, head SHA, PR URL, ticket, CI state, each read from tools in this turn.
3. Verified, with the evidence (command and result, or link); then claimed but not verified, labelled as such.
4. Decisions made and alternatives rejected, one line each.
5. The next action, concrete enough to start without reading the transcript; then the remaining steps.
6. Gotchas: wrong turns, flaky checks, access gaps, rules the next agent will trip on.
7. Open questions that only the user can settle.

No transcript dumps or diffs; point to files and commits.
Run `~/.config/my-ai-config/scripts/workflow/prose-lint.py` on the note.
When the user asked for cleanup too, run `~/.config/my-ai-config/scripts/workflow/worktree-audit.py` and prune only after reading its table.

## Resume

Read the note, then the branch log and diff against `origin/<base>`.
The note is a set of claims: re-check state (head, PR, CI, ticket, claims) live before acting, but do not redo work whose evidence still resolves.
Claim the branch before the first edit.
Name the resume point, then continue with the note's next action under the normal rules for that kind of work.
Report what you inherited, what you re-checked, and anything in the note that was wrong.

Adapted from Lauren Tan's Pause safely, Session pickup and Worktree cleanup playbooks; provenance and licence: `~/.config/my-ai-config/upstream/pstack/README.md`.
