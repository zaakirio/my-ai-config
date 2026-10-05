# Claude Code

The installer links shared skills into `~/.claude/skills` and reviewer definitions into `~/.claude/agents`.
Use `/zk-review`, `/zk-fix`, or `/team`, or name the skill in a request.
Additional seats are explicit installer `--claude-profile` paths; forward the active `CLAUDE_CONFIG_DIR` when launching a child CLI.
Use native agent tools if exposed; read each review prompt at `~/.config/my-ai-config/agents/<name>.md` if that agent is not registered.
The model/tool/color frontmatter in those files is Claude metadata; other clients use the prompt body.
Do not add permission-bypass flags when launching children.
