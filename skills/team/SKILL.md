---
name: team
description: Coordinate an engineer and an independent reviewer when explicitly asked for a team, delegation, or an engineer/QA loop. Supports native workers and optional persistent Herdr panes.
---

Read `~/.config/my-ai-config/adapters/README.md`, then only the current runtime adapter.
Keep lead, engineer and QA responsibilities separate; the lead owns the result and the integration decision.
Give each writer an isolated branch/worktree and explicit file scope.
Do not let workers switch or commit into a shared checkout.
For persistent work in Herdr, use its adapter; short read-only reviews may use native workers.
Do not replace a requested durable team with ephemeral workers without stating the loss of resumability.

Pass the matching prompt from `reference/` plus the task, accepted behavior, source identity and evidence destination.
Engineer implements and verifies; QA checks the exact candidate and tries the failure paths without editing it.
Use a different available model when configured; model diversity is not evidence by itself.
A run with no independent worker cannot claim independent PASS.

Protocol: `DONE <branch> <evidence>`, `REVIEW <branch> <sha> <evidence>`, `PASS <sha> <proof>`, `FAIL <sha> <repro>`, `BLOCKED <reason>`.
Use the runtime's native message/wait tools, not invented shell commands.
Merge only after independent PASS on the candidate and within the user's existing authorization.
Invoke `zk-review` for a requested PR review and `zk-fix` for authorized feedback fixes.
Finish with outcome, evidence and any remaining acceptance gap.
