# Persistent Herdr teams

Use only for an explicitly requested Herdr team when `HERDR_ENV=1`.
Resolve available model names with the installed client before using the historical defaults below.

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
TEAM_ENV=(); [ -n "$CLAUDE_CONFIG_DIR" ] && TEAM_ENV=(--env "CLAUDE_CONFIG_DIR=$CLAUDE_CONFIG_DIR")   # same seat as the lead
TR=$(herdr pane split --current --direction right --ratio 0.5 --cwd "$PWD" --no-focus "${TEAM_ENV[@]}" | jq -r .result.pane.pane_id)   # top-right
BL=$(herdr pane split --current --direction down  --ratio 0.5 --cwd "$PWD" --no-focus "${TEAM_ENV[@]}" | jq -r .result.pane.pane_id)   # bottom-left
BR=$(herdr pane split $TR      --direction down  --ratio 0.5 --cwd "$PWD" --no-focus "${TEAM_ENV[@]}" | jq -r .result.pane.pane_id)   # bottom-right
```

Re-gridding panes that already exist: `herdr pane move` within the same tab is a no-op (`changed: false`), so bounce the pane through a new tab and back:

```bash
herdr pane move <id> --new-tab --no-focus
herdr pane move <id> --tab <lead tab id> --target-pane <pane to sit under> --split down --ratio 0.5 --no-focus
```

The terminal keeps its id, so the agent in it survives. Tab id is in `herdr pane current` at .result.pane.tab_id.

Seat the agents: eng-1 in $TR, qa in $BR, a second engineer in $BL. With one engineer, skip the $BL split. More than three agents: split the engineer panes down again rather than adding columns.

herdr agent start eng-1 --kind claude --pane $TR -- --model fable --effort low
herdr agent start qa    --kind claude --pane $BR -- --model opus  --effort low
herdr agent prompt <name> <text>
herdr agent wait <name> --until idle --timeout <ms>   # never poll
herdr agent read <name>

Read the selected role at `~/.config/my-ai-config/skills/team/reference/<role>.md` and pass that prompt to the worker.
Choose a separate worktree and branch for each writer; never switch the user's shared checkout.
Protocol: DONE <branch> <evidence> | REVIEW <branch> <summary> <evidence> | BLOCKED <reason> | PASS <proof> | FAIL <repro> <expected>.
Lead merges only on PASS. More herdr: herdr --skill.
