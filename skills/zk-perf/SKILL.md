---
name: zk-perf
description: Measure and improve a concrete latency, throughput or resource bottleneck. Use for performance work and measured speedup claims; not generic code cleanup.
---

Choose a user-visible workload and metric before changing code.
Read the measurement command and prove that the intended work completes with correct outputs and counted failures.
Use comparable production configurations and data; record cold/warm cache state.
Profile separately from timing to identify the limiting work.
For a comparison, alternate baseline and candidate for at least five runs per side and report median plus range.
A requested rough estimate may use one run if clearly labelled; it cannot select a winner.
Try removing unused work, avoiding repeated work and deferring noncritical work before adding concurrency.
For sustained optimization, freeze the measurement command and regression gate, then change one hypothesis at a time.
Keep only improvements beyond noise that preserve behavior; record rejected attempts too.
Do not treat faster failures, skipped work or lowered correctness requirements as wins.
Report the measured result, limiter, command and raw results; use inconclusive when the comparison is not valid.

Adapted from Lauren Tan's `benchmark-checklist` and Hillclimb playbook; provenance and licence: `~/.config/my-ai-config/upstream/pstack/README.md`.
