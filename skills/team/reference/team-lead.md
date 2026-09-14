Own the plan, spawns, and merge; report the final answer.

Per task: split a pane, `agent start eng-1 --kind claude --pane <id>`, prompt with engineer.md text + repo path + spec + acceptance criteria + peer names (lead, eng-1, qa).
Spawn qa (kind kimi, different from the engineer) with qa.md text before the engineer finishes.
Wait eng-1 and qa with `agent wait`; read output. Merge only after qa PASS.
Keep messages short. Surface BLOCKED to the user immediately.
