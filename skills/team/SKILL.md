---
name: team
description: Spawn engineer and QA agents in herdr panes and coordinate them by prompt. Use when asked to form a team, delegate to agents, or run an engineer/QA loop.
---

Requires HERDR_ENV=1.

herdr pane split --current --direction right --cwd "$PWD" --no-focus   # new id at .result.pane.pane_id
herdr agent start <name> --kind <claude|pi|kimi> --pane <id> [-- <agent args>]
herdr agent prompt <name> <text>
herdr agent wait <name> --until idle --timeout <ms>   # never poll
herdr agent read <name>

Roles: lead (caller), one eng-* per task, qa on a different kind than the engineer. Paste reference/<role>.md into the spawn prompt.
Protocol: DONE <branch> <evidence> | REVIEW <branch> <summary> <evidence> | BLOCKED <reason> | PASS <proof> | FAIL <repro> <expected>.
Lead merges only on PASS. More herdr: herdr --skill.
