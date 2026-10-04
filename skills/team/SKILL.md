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

First, name yourself so peers can `herdr agent prompt lead`; without this every DONE/PASS/FAIL addressed to lead is dropped:

```bash
herdr agent rename "$(herdr pane current | jq -r .result.pane.pane_id)" lead
```

Layout: a 2x2 grid, lead top-left. Split the lead pane right, then split the lead pane down, then split the new right pane down. Each result's id is at .result.pane.pane_id.

```bash
ENV=(); [ -n "$CLAUDE_CONFIG_DIR" ] && ENV=(--env "CLAUDE_CONFIG_DIR=$CLAUDE_CONFIG_DIR")   # same seat as the lead
TR=$(herdr pane split --current --direction right --ratio 0.5 --cwd "$PWD" --no-focus "${ENV[@]}" | jq -r .result.pane.pane_id)   # top-right
BL=$(herdr pane split --current --direction down  --ratio 0.5 --cwd "$PWD" --no-focus "${ENV[@]}" | jq -r .result.pane.pane_id)   # bottom-left
BR=$(herdr pane split $TR      --direction down  --ratio 0.5 --cwd "$PWD" --no-focus "${ENV[@]}" | jq -r .result.pane.pane_id)   # bottom-right
```

Re-gridding panes that already exist: `herdr pane move` within the same tab is a no-op (`changed: false`), so bounce the pane through a new tab and back:

```bash
herdr pane move <id> --new-tab --no-focus
herdr pane move <id> --tab <lead tab id> --target-pane <pane to sit under> --split down --ratio 0.5 --no-focus
```

The terminal keeps its id, so the agent in it survives. Tab id is in `herdr pane current` at .result.pane.tab_id.

Seat the agents: eng-1 in $TR, qa in $BR, a second engineer in $BL. With one engineer, skip the $BL split. More than three agents: split the engineer panes down again rather than adding columns.

herdr agent start eng-1 --kind claude --pane $TR -- --model fable --effort low --dangerously-skip-permissions
herdr agent start qa    --kind claude --pane $BR -- --model opus  --effort low --dangerously-skip-permissions
herdr agent prompt <name> <text>
herdr agent wait <name> --until idle --timeout <ms>   # never poll
herdr agent read <name>

Paste reference/<role>.md into the spawn prompt.
Protocol: DONE <branch> <evidence> | REVIEW <branch> <summary> <evidence> | BLOCKED <reason> | PASS <proof> | FAIL <repro> <expected>.
Lead merges only on PASS. More herdr: herdr --skill.
