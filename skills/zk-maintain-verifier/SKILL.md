---
name: zk-maintain-verifier
description: Check an existing project's verification skill and feature map against code and live behavior. Use for verifier upkeep or drift audits; not feature implementation.
---

Locate the existing verifier, its feature map and owned helper scripts.
Read recent changes only for affected features; check the index for missing routes and broken references.
For a full maintenance pass, exercise every mapped feature live, coalescing compatible journeys into one healthy session.
Re-check health after a surprising result; reset a wedged UI before continuing.
Keep one owner for a shared device; readers may inspect source independently.
Distinguish documentation drift, harness gaps and product regressions.
For a changed visual baseline or release target, check the mapped evidence against `~/.config/my-ai-config/review/target-proof.md`; an old build or a different screen cannot clear the check.
A journey whose precondition the seed data lacks is a harness gap reported as a failure, never a journey to weaken until it passes.
Fix proven documentation/harness drift and rerun the affected path; report product regressions separately unless fixing them is also authorized.
Preserve evidence across cleanup and stop only processes owned by the run.
Report clean, changed, or incomplete, with exact coverage and missing prerequisites.
No scheduled task, PR or remote message is created merely by invoking this skill.

Adapted from Lauren Tan's `maintain-verification-skill`; provenance and licence: `~/.config/my-ai-config/upstream/pstack/README.md`.
