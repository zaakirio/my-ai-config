# Bot finding dismiss patterns

Read by `zk-fix` before it disputes an automated review finding.
A pattern tells you what to check, never what to conclude: the dispute still needs the check's result in the reply.
Adapted from the bugbot triage reference in Lauren Tan's pstack.

Add a pattern only after a real dismissal held up, in this shape:

```
### <short name>
- Confidence: candidate | recurring | strong
- Skip when: <conditions that must all be true and checked>
- Do not skip when: <risk boundaries>
- Signal: <phrases or code context that identify it>
- Source: <PR or comment URL>
```

Use `candidate` for one or two cases, `recurring` after several dismissals that held, and `strong` only for a narrow, repeatedly verified, low-risk pattern.

### Intentional visual change

- Confidence: candidate
- Skip when: the PR description, screenshots or ticket make the visual change explicit and the finding only restates that a shared default changed.
- Do not skip when: it points at accessibility, focus visibility, keyboard navigation, contrast, or a component API contract the PR did not mean to change.
- Signal: comments about spacing, sizes or outlines on a PR whose stated goal is that visual change.

### Usage the bot cannot see

- Confidence: candidate
- Skip when: the symbol flagged as unused is used by a later PR in the same stack, and that PR's diff shows it.
- Do not skip when: the PR is not in a stack, the symbol is public API, or the later use cannot be shown.
- Signal: "exported but never used" on a stacked PR.

### Temporary duplication during a migration

- Confidence: candidate
- Skip when: the duplicate keeps a new path parallel to an old path that the ticket or a linked PR deletes.
- Do not skip when: the duplicate touches security, billing, data access or API behavior, or no deletion is tracked.
- Signal: "duplicated logic" where the old path has a tracked removal.

### Invariant already enforced

- Confidence: candidate
- Skip when: a shared component, framework contract, type or single source of truth in the tree already guarantees what the finding asks for, and you can cite the `file:line`.
- Do not skip when: the invariant is assumed but not enforced, depends on timing, or crosses an async or state boundary.
- Signal: requests for a guard that the type or the caller already makes impossible.
