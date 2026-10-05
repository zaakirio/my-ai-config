---
name: zk-correct
description: Prevent repeated agent mistakes with a structural fix and a demonstrated failing control. Use when the user asks to stop recurring mistakes or improve workflow reliability, not for ordinary one-off fixes.
---

Find repeated mistake classes in the current project's commits, reviews and corrections.
Require concrete occurrences; do not search unrelated chat history or invent recurrence.
Prefer one owner or one supported API, then types, then a narrow lint/CI check, then a behavioral regression test.
Reuse an existing checker where possible.
Run the check against a retained bad case and the corrected case; a check that only ever passed has not proved prevention.
Name the corrective action in the failure message.
Keep judgment calls in short instructions; do not add a new rule for a mistake already made impossible by code.
Change only the authorized project and workflow; new publishing or broad migrations need their own task scope.
Report the mistake, evidence, enforcement and red/green command.

Adapted from Lauren Tan's `correct`; provenance and licence: `~/.config/my-ai-config/upstream/pstack/README.md`.
