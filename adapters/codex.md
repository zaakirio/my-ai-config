# Codex

The installer links shared skills into `~/.agents/skills` and rules into `~/.codex/AGENTS.md`.
Invoke a skill by name, or use `$zk-review`, `$zk-fix`, or `$team` where the client provides skill mentions.
Use the session's native delegation capability when available and authorized by the selected workflow.
For a named review role, give the worker the absolute path to `~/.config/my-ai-config/agents/<name>.md` and instruct it to read the prompt body.
Claude frontmatter does not register a Codex agent or select its model.
If delegation is unavailable, follow the shared adapter's serial fallback; do not change global feature flags to force it on.
