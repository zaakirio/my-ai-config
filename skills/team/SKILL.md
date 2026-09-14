---
name: team
description: Spawn engineer and QA agents in herdr panes and coordinate them by prompt. Use when asked to form a team, delegate to agents, or run an engineer/QA loop.
---

Requires HERDR_ENV=1.

Roles and models (all Claude Code):
- lead: the caller. Fable, effort high (`claude --model fable --effort high`).
- eng-*: one per task. Fable, effort low.
- qa: Opus, effort low. Different model from the engineer so it does not share its blind spots.

herdr runs the bare `claude` executable, not the shell alias, so pass flags explicitly.
If the lead has CLAUDE_CONFIG_DIR set (claude2 seat), forward it so spawned agents bill the same seat.

herdr pane split --current --direction right --cwd "$PWD" --no-focus   # new id at .result.pane.pane_id
[ -n "$CLAUDE_CONFIG_DIR" ] && herdr pane run <id> "export CLAUDE_CONFIG_DIR=$CLAUDE_CONFIG_DIR"
herdr agent start eng-1 --kind claude --pane <id> -- --model fable --effort low --dangerously-skip-permissions
herdr agent start qa    --kind claude --pane <id> -- --model opus  --effort low --dangerously-skip-permissions
herdr agent prompt <name> <text>
herdr agent wait <name> --until idle --timeout <ms>   # never poll
herdr agent read <name>

Paste reference/<role>.md into the spawn prompt.
Protocol: DONE <branch> <evidence> | REVIEW <branch> <summary> <evidence> | BLOCKED <reason> | PASS <proof> | FAIL <repro> <expected>.
Lead merges only on PASS. More herdr: herdr --skill.
