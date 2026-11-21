---
name: zk-interrogate
description: Adversarial review of your own change or design before it ships, keeping only findings that a run proves. Use for "interrogate", "adversarial review", "tear this apart", "stress test this", "find blind spots", "spawn sub-agents to try to break it", or before opening a PR on risky work. Reports only; it does not fix or post anything.
---

Scope is what the user names; otherwise the branch diff from its merge base with `origin/<base>` through the working tree.
State the intent in one paragraph from the request, the ticket, the commits and the PR body; ask only if it is unclear.

Spawn 2-4 adversaries in parallel, each in its own worktree or scratch directory with the uncommitted changes copied in.
Use more than one model family when the runtime offers one, for example a Codex child through T3 `delegate_task`; say when only one family was available.
Give each adversary the scope, the intent, `~/.config/my-ai-config/review/verification.md`, and this brief:

```
Break this change. Prove each finding with a run against the real code: a failing test,
a repro script, or command output that shows the wrong behavior. For a design, run a probe
or prototype. Report each finding with a title, the exact command, the output it printed,
and the output the intent requires. Leave out anything you did not run, including style,
naming, structure and risks that need a future change to matter. No findings is valid.
```

Rerun every reported command yourself at the current head.
Keep a finding only when the output shows the failure and the failure breaks the intent; merge findings that share a root cause.

Report: the intent, each kept finding with command, output, the broken intent and which adversaries found it, then per adversary the count dropped and why.
Remove the adversaries' worktrees after the report unless a kept finding needs its repro.

Adapted from Lauren Tan's `interrogate`; provenance and licence: `~/.config/my-ai-config/upstream/pstack/README.md`.
