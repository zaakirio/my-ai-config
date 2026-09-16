# my-ai-config

Personal AI agent config. Source of truth; symlink into place on a new machine.

- `agents.md`: global agent rules (claude reads it via `~/.claude/CLAUDE.md`).
- `herdr/`: `config.toml` (theme, sidebar layout), `sidebar-meta.py` + plist (custom sidebar tokens `$tabs/$panes/$git/$elapsed`).
- `skills/team/`: lead/engineer/QA agents coordinating through herdr panes.
- `skills/review-pr/`, `skills/fix-pr/`: PR review and review-response, fanning out to the reviewer agents below.
- `agents/review-*.md`: the six reviewer personas the review skill spawns in parallel, including security and performance specialists gated on diff signals.
- `review/`: shared references both skills read at the step that needs them, plus `post-review.py`, first-party language patterns (`typescript.md`, `go.md`, `react.md`), and vendored security checklists under `review/reference/`.

## Install

```sh
ln -sf "$PWD/agents.md" ~/.config/agents.md
ln -sf "$PWD/herdr/config.toml" ~/.config/herdr/config.toml
ln -sf "$PWD/herdr/sidebar-meta.py" ~/.config/herdr/sidebar-meta.py
ln -sf "$PWD/herdr/dev.herdr.sidebar-meta.plist" ~/Library/LaunchAgents/dev.herdr.sidebar-meta.plist
mkdir -p ~/.agents/skills ~/.claude/skills ~/.claude/agents
for s in team review-pr fix-pr; do
  ln -sfn "$PWD/skills/$s" ~/.agents/skills/$s
  ln -sfn "$PWD/skills/$s" ~/.claude/skills/$s
done
for a in "$PWD"/agents/*.md; do ln -sf "$a" ~/.claude/agents/; done
ln -sfn "$PWD/review" ~/.claude/review         # skills and agents read from this path
ln -sfn ~/.claude/skills ~/.claude-b/skills    # second seat (claude2)
```

Reload herdr after config changes: `herdr server reload-config`.

## PR review

`/review-pr [PR | TICKET-KEY | URL]` fetches the PR and its diff to disk, checks the PR head out into a worktree, pulls acceptance criteria from Jira or Linear, runs the six reviewer agents in parallel, verifies what they report against the head tree, then posts inline comments and a verdict. It approves only when nothing critical or important survives verification; `--local` posts nothing and `--no-approve` caps the verdict at a comment.

`/fix-pr [PR]` does the other direction: fetch the review comments, separate actionable from needs-a-human, apply the fixes, and reply to every finding as Fixed, Deferred, Investigated or Disputed. It edits the working tree and stops; `--commit`, `--push` and `--reply` are opt-in.

Under `/team`, the lead runs `/review-pr` and maps the verdict onto the PASS/FAIL protocol; the engineer runs `/fix-pr` against a FAIL.

The reference the whole thing rests on is `review/verification.md`: ten checks, each added after a real failure, that stop a review asserting what it has not verified. Beside it, `review/diagnosis.md` separates a defect's trigger from the condition masking it, and `review/decision-authority.md` draws the line between a finding the reviewer settles and one that goes to a human.

Two invariants are enforced in `review/post-review.py` rather than in prose, because prose fails silently on a long run: it refuses to post against a head that has moved, and refuses an approve carrying a critical, an important, or an unverified finding.

### Environment

| Variable | For |
|---|---|
| `GITHUB_TOKEN` or `gh auth login` | GitHub |
| `BITBUCKET_TOKEN` | Bitbucket, an Atlassian API token used with `git config user.email` |
| `LINEAR_API_KEY` | Linear, sent raw with no `Bearer` prefix |
| `JIRA_API_TOKEN`, `JIRA_EMAIL`, `JIRA_INSTANCE` | Jira |
| `TICKET_PROVIDER`, `LINEAR_TEAM_KEYS`, `JIRA_PROJECT_KEYS` | optional, skips provider probing in a workspace running both trackers |

Everything degrades: no ticket provider means the code is still reviewed and the summary says ticket context was unavailable. A host that cannot be reached is reported, never worked around.
