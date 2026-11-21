# my-ai-config

One portable source for personal rules, skills, review prompts and scripts.
Shared workflows use the Agent Skills format; thin [runtime adapters](adapters/README.md) explain client-specific discovery and delegation.
The entire bundle is installed at `~/.config/my-ai-config`, so shared references do not depend on Claude or the checkout location.

## Install and verify

Requires Python 3 and Git on macOS or Linux.
Clone this repository anywhere, then run from its root:

```sh
python3 scripts/config.py install --dry-run
python3 scripts/config.py install
python3 scripts/config.py doctor
```

The default targets are Codex, Claude Code, OpenCode and Pi.
Use `--clients codex claude cursor` to select targets; Cursor receives skills, while its rules remain under your existing Cursor configuration.
Additional Claude seats use repeatable `--claude-profile ~/.claude-b` arguments on both install and doctor.
Rerunning installation is safe and discovers new skills automatically.
A conflict stops the whole plan before links change; inspect it and use `--replace` to retain a dated backup before replacement.
Existing unrelated skills/settings remain untouched.
Use `--home /tmp/clean-agent-home` to test installation without changing your real home.
Move the checkout by rerunning installation from its new path with `--replace`; do not copy only `SKILL.md` files.
Start a fresh client session if new skills are not discovered.

`agents.md` is the only global rule source, including delivery rules previously held separately in `~/.config/agents.md`.
The installer links that legacy path too, preserving existing Claude seat links.
The optional macOS Herdr sidebar remains in `herdr/`; it is not required for any portable skill.
For a Herdr team, follow [its runtime adapter](adapters/herdr.md).

## Local resource guard

Linux heavy jobs share a nonblocking lock and a default 10 GiB disk reserve.
Estimate new writes before running; use a larger estimate for fresh dependencies, build layers and browser downloads.
The lock covers cooperating commands only; inspect existing unmanaged processes before cleanup.

```sh
python3 scripts/workspace.py check --required-gib 6
python3 scripts/workspace.py run --required-gib 6 -- npm ci
python3 scripts/workspace.py run --required-gib 1 --pin -- python3 verify.py
python3 scripts/workspace.py prune
```

Commands receive `AGENT_ARTIFACT_DIR` for temporary evidence.
Only completed runs in `~/.cache/agent-work/runs` older than seven days expire.
`.keep` pins a run; remove it only after retaining the compact acceptance proof.
Completion records remain in `~/.cache/agent-work/records`.
Aborted runs without a completion record require manual review; no arbitrary temporary folder, worktree, package cache, chat record or database is pruned.
Command arguments and output are not stored by the guard.

If preflight refuses a job, inspect live registered worktree sizes before choosing what to do:

```sh
python3 scripts/workflow/worktree-audit.py --offline --include-primary --base origin/dev ~/dev/LingoBite
```

Use the actual integration ref for the project.
Sizes include ignored files and, in the primary checkout, the Git database; they are not reclaimable-byte estimates.

Enable daily retention on this Linux host:

```sh
mkdir -p ~/.config/systemd/user
ln -s ~/.config/my-ai-config/systemd/agent-artifacts.service ~/.config/systemd/user/agent-artifacts.service
ln -s ~/.config/my-ai-config/systemd/agent-artifacts.timer ~/.config/systemd/user/agent-artifacts.timer
systemctl --user daemon-reload
systemctl --user enable --now agent-artifacts.timer
```

## Skills

| Skill | Use |
| --- | --- |
| `zk-review` | Requested PR review with ticket context, independent lenses and verified findings |
| `zk-fix` | Apply requested review feedback; commit, push and replies remain opt-in |
| `team` | Explicit engineer/QA coordination with isolated writers |
| `zk-correct` | Prevent a repeated mistake with a proven structural check |
| `zk-blast-radius` | Prove a shared change's key safety assumption |
| `zk-perf` | Measure a real bottleneck and retain only verified wins |
| `zk-create-verifier` | Build a project-owned runtime verification skill from existing tools |
| `zk-maintain-verifier` | Check verifier instructions against source and live behavior |
| `zk-interrogate` | Adversarial review of your own change, keeping only run-proven findings |
| `zk-handover` | Pause or wrap up so another agent can resume cold, and resume from such a note |
| `zk-reflect` | Turn a session's lessons into approved, tested skill edits |

Use the skill's name in a request; exact menu syntax differs by client and is documented in its adapter.
Reviewer prompts live in `agents/`; Claude can register them natively, while other clients read the same prompt bodies through their available workers.
No adapter assumes that installing Markdown provides a new model, subagent tool, cloud machine or scheduler.
Project feature maps and delivery commands stay in each project's repository.
For visual and release tasks, use the [target-proof recipe](review/target-proof.md) for the first handback and the pilot measures.
For a disputed fix, use the [paired-revision check](review/diagnosis.md#reviewing-a-fix) before editing.

## Review and feedback

`zk-review` checks the exact PR head, resolves ticket criteria, verifies findings and rechecks the remote head before posting.
Use `--local` for a local report and `--no-approve` to cap a posted verdict at COMMENT.
`zk-fix` edits and stops by default; `--commit`, `--push` and `--reply` are additive opt-ins.
[Verification](review/verification.md), [diagnosis](review/diagnosis.md) and [decision authority](review/decision-authority.md) remain the evidence contract.
`review/post-review.py` mechanically refuses stale-head posts and approvals with blocking or unverified findings.

Credentials remain outside this repository: GitHub uses `gh auth login` or `GITHUB_TOKEN`; Bitbucket uses `BITBUCKET_TOKEN`; Linear uses `LINEAR_API_KEY`; Jira uses `JIRA_API_TOKEN`, `JIRA_EMAIL`, and `JIRA_INSTANCE`.
See [host calls](review/hosts.md) and [ticket resolution](review/tickets.md) when needed.

## Lauren's upstream

Selected workflows are adapted directly from [Lauren Tan's pstack](https://github.com/cursor/plugins/tree/main/pstack), not a community port.
[Source provenance](upstream/pstack/README.md) includes the pinned revision, unchanged originals, hashes, adaptation map and MIT notice.

```sh
python3 scripts/check-upstream.py --offline
python3 scripts/check-upstream.py
python3 -m unittest discover -s tests -v
```

The network check reports changes only; it never installs or executes remote instructions. It uses `gh api` when `gh` is installed, because some proxies block git and raw file downloads.
Review upstream changes before refreshing the pin.

## Workflow scripts

```sh
python3 scripts/workflow/worktree-audit.py --scan ~/.t3/worktrees <repo> ...
python3 scripts/workflow/worktree-audit.py --scan ~/.t3/worktrees --prune
python3 scripts/workflow/prose-lint.py pr-body.md
```

`worktree-audit.py` sorts linked worktrees by size and reports the primary checkout separately with `--include-primary`.
Git-locked trees stay held, observed Linux process working directories count as activity, and an unreadable Git status cannot qualify as clean.
`--prune` removes only `safe` worktrees: clean, merged or with a closed PR, no commit, checkout or reset within `--recent-hours` (default 72), and with no `pr-owner` claim.
Branches survive, so `git worktree add <path> <branch>` restores a pruned worktree.
`prose-lint.py` flags dashes, blockquotes, AI attribution, AI vocabulary and chatbot phrases outside code fences, and exits 1 with the fix for each hit.
