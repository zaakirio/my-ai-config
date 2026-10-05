---
name: zk-blast-radius
description: Prove a change's key safety assumption across consumers, persisted data and runtime boundaries. Use for shared-contract changes, compatibility changes, or an explicit impact assessment.
---

State the changed behavior and the one assumption on which its safety depends.
Follow callers, serialized bytes, stored records, generated consumers, platform variants and teardown timing that a symbol search misses.
Check the actual pinned library implementation where its semantics matter.
Run the smallest real-code control that can disprove the assumption.
For UI or process ownership changes, include the running surface and the replacement/retry path.
Separate confirmed risk, cleared risk and unproven assumptions; no list of hypothetical warnings.
Feed the result into the existing review workflow rather than starting a second review process.
Return the assumption, its evidence and the cheapest missing proof.

Adapted from Lauren Tan's `blast-radius`; provenance and licence: `~/.config/my-ai-config/upstream/pstack/README.md`.
