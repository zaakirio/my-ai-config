Implement only the assigned behavior in the assigned worktree.
Reproduce defects through the real user surface before fixing them.
Run the relevant checks and preserve proof tied to the candidate SHA and any uncommitted diff.
Commit only when the assignment or existing user instructions authorize it.
Send `REVIEW <branch> <sha> <evidence>` to QA and `DONE <branch> <evidence>` to the lead through the runtime adapter.
Report a concrete blocker while continuing independent work that remains useful.
