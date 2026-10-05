# Runtime adapters

The shared workflow lives in `skills/`, review prompts in `agents/`, and evidence rules in `review/`.
The installer makes the entire bundle available at `~/.config/my-ai-config`; copy or clone the bundle, not individual skill directories whose references would be missing.
These are user-level paths, independent of the checkout location and username.
Resolve that link to an absolute path before passing references to a worker.

Read only the adapter for the current client: [Claude](claude.md), [Codex](codex.md), [OpenCode](opencode.md), [Pi](pi.md), or [Cursor](cursor.md).
For an explicitly requested persistent Herdr team, also read [Herdr](herdr.md).

Inspect the tools actually exposed in this session before selecting a delegation method.
An installed executable does not prove native delegation or a particular model is available.
Use the user's configured model; select another only when the task or user calls for it and the client exposes it.
Report same-model review honestly; do not call it cross-model review.
If independent workers are unavailable, perform the checks serially and report that independent review remains outstanding.
Do not manufacture a PASS from self-review when an independent verdict is required.

Use native progress and work tracking when available; no universal tool names or background scheduling are assumed.
User authorization for commits, push, review posting and deployment remains unchanged across adapters.

Discovery references: [Agent Skills](https://agentskills.io/specification), [Claude](https://code.claude.com/docs/en/skills), [Codex](https://learn.chatgpt.com/docs/build-skills), [OpenCode](https://opencode.ai/docs/skills/), [Pi](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md), [Cursor](https://cursor.com/docs/skills).
