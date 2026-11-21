---
name: zk-create-verifier
description: Build a project-local verification skill around the project's existing runtime and checks. Use when asked to create a repeatable way for agents to drive and verify an app or service.
---

Read the project's current instructions, manifests and check runners before inventing commands.
Identify the actual user surface, startup/cleanup, isolated data and credentials, health check and observable end state.
Launch must reach a usable state from an empty data dir, including migrations and seed data; ready means usable, not just that a process answers.
When seed data lacks a journey's precondition, the journey reports failure and the feature's gotchas say why; never weaken a journey to make it pass.
Reuse existing CLIs and fixtures; add only missing controls with descriptive errors and bounded execution.
Put the skill and a small feature map in the project's skill directory, not the personal configuration bundle.
Each feature names its user entry point, control command, expected observation, evidence tier and prerequisites.
For visual and release checks, add only the applicable fields from `~/.config/my-ai-config/review/target-proof.md` to the project feature map.
Make source, real-process, device and deployment evidence visibly distinct.
Keep raw artifacts outside the skill; record source identity and artifact hashes with each result.
Prove the workflow on one mapped feature from launch through verification and cleanup.
If you proved it in a stand-in for the real target (a container for a fresh VM, a local stack for a remote one), list each setup step the stand-in did that the target will not; those stay unverified until a run on the real target covers them.
Confirm evidence survives cleanup and owned processes do not.
If the required runtime is unavailable, deliver the working source checks and state that the live driver is unverified; do not label a draft a verified app driver.
Read the current runtime adapter only when choosing discovery paths or delegation.

Adapted from Lauren Tan's `create-verification-skill` and Build the Lever; provenance and licence: `~/.config/my-ai-config/upstream/pstack/README.md`.
