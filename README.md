# my-ai-config

Personal AI agent config. Source of truth; symlink into place on a new machine.

- `agents.md`: global agent rules (claude reads it via `~/.claude/CLAUDE.md`).
- `herdr/`: `config.toml` (theme, sidebar layout), `sidebar-meta.py` + plist (custom sidebar tokens `$tabs/$panes/$git/$elapsed`).
- `skills/team/`: lead/engineer/QA agents coordinating through herdr panes.

## Install

```sh
ln -sf "$PWD/agents.md" ~/.config/agents.md
ln -sf "$PWD/herdr/config.toml" ~/.config/herdr/config.toml
ln -sf "$PWD/herdr/sidebar-meta.py" ~/.config/herdr/sidebar-meta.py
ln -sf "$PWD/herdr/dev.herdr.sidebar-meta.plist" ~/Library/LaunchAgents/dev.herdr.sidebar-meta.plist
mkdir -p ~/.agents/skills ~/.claude/skills
ln -sfn "$PWD/skills/team" ~/.agents/skills/team
ln -sfn "$PWD/skills/team" ~/.claude/skills/team
ln -sfn ~/.claude/skills ~/.claude-b/skills   # second seat (claude2)
```

Reload herdr after config changes: `herdr server reload-config`.
