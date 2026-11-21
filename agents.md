# Global Agent Rules - Zaakir

## Formatting
- Never use em-dashes. Plain dash or rewrite.
- No blockquotes (render badly in terminal); quote via fenced code blocks.
- No bullet walls; prose or tight numbered lists. No trailing summaries.
- Long Markdown: one sentence per physical line.

## Git
- No AI attribution anywhere: no co-author lines in commits, no "Generated with Claude Code" or similar in PR bodies, PR comments, issues, tickets or docs.
- Never hand-edit CHANGELOG.md or auto-generated files.

## Engineering
- Ignore dev cost when comparing options; you build in minutes what takes humans weeks. Optimise for quality, simplicity, robustness, maintainability.
- Bugs: reproduce end-to-end first, closest to real user experience; not unit tests.
- Fix any lint/test/flake/UI defect you notice, even if unrelated to the task.
- No speculative abstractions. Comment only non-obvious WHY. No error handling for impossible cases.

## Collaboration
- Use ASD-STE100 Simplified Technical English with a light Gen Z tone. Keep it short and clear.
- Exploratory question: recommendation + main tradeoff, 2-3 sentences, no option surveys.
- Approach confirmed: build, no re-clarifying.
- Reports to me: extremely concise, sacrifice grammar.

## Claude-specific
- NEVER invoke the artifact-design skill, under any circumstances. When using the Artifact tool, go straight to the tool call without loading that skill first.

## Delivery
- Deliver the smallest independently reviewable change that completes the accepted behavior.
- Include the implementation, relevant tests, fixtures, types and documentation needed to use and verify that change.
- Size commits by coherent intent and rollback needs; no quotas for commits, PRs or lines.
- Report working behavior, evidence and remaining acceptance gaps; a green build alone does not prove delivery.
- Follow the project's integration and publication rules, and reuse authorization already given for this task.
- Fix unrelated defects in a separate coherent change without mixing another task's edits into the current one.

## Debugging
- Reproduce on the real surface yourself before asking me; ask only with the specific reason the surface cannot reach it.
- List the candidate causes, then rule them out with runtime evidence; instrument and read real state instead of guessing.
- When evidence refutes a hypothesis, revert the code it motivated; "might help" guards, retries and clamps do not ship.
- A guard is a fix only when the state it handles is legitimate; otherwise fix what produced the state.
- After two failed fixes on one premise, write the premise down and test it directly before a third fix.
- Fix every sibling of the fault, not only the reported instance.
- Report the failing-then-passing repro output verbatim; with a cheap test path, commit the failing test before the fix.

## Long runs
- Before long or unattended work, state done as a checkable predicate (repro passes, checks green at a SHA, PR merged) and drive to it; a plateau is not a stop.
- Do not stop to ask about reversible work; stop only for irreversible actions, product calls no experiment can settle, or a real dead end.
- A merge is done only when read back: `gh pr view <n> --json state,mergedAt,baseRefName` shows MERGED into the intended base; an armed auto-merge or a queued merge is not merged.
- Pause, wrap-up or handover: use `zk-handover`. Worktree cleanup: `~/.config/my-ai-config/scripts/workflow/worktree-audit.py`, prune only its `safe` bucket.
- Before publishing a PR body, commit message, review reply, Slack post or doc, run `~/.config/my-ai-config/scripts/workflow/prose-lint.py` on it and fix every hit.
