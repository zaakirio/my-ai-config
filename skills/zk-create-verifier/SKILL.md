---
name: zk-create-verifier
description: Build a project-local verification skill around the project's existing runtime and checks. Use when asked to create a repeatable way for agents to drive and verify an app or service.
---

Read the project's current instructions, manifests and check runners before inventing commands.
Identify the actual user surface, startup/cleanup, isolated data and credentials, health check and observable end state.
Reuse existing CLIs and fixtures; add only missing controls with descriptive errors and bounded execution.
Put the skill and a small feature map in the project's skill directory, not the personal configuration bundle.
Each feature names its user entry point, control command, expected observation, evidence tier and prerequisites.
Make source, real-process, device and deployment evidence visibly distinct.
Keep raw artifacts outside the skill; record source identity and artifact hashes with each result.
Prove the workflow on one mapped feature from launch through verification and cleanup.
Confirm evidence survives cleanup and owned processes do not.
If the required runtime is unavailable, deliver the working source checks and state that the live driver is unverified; do not label a draft a verified app driver.
Read the current runtime adapter only when choosing discovery paths or delegation.

Adapted from Lauren Tan's `create-verification-skill` and Build the Lever; provenance and licence: `~/.config/my-ai-config/upstream/pstack/README.md`.
