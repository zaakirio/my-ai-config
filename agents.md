# Global Agent Rules - Zaakir

## Formatting
- Never use em-dashes. Plain dash or rewrite.
- No blockquotes (render badly in terminal); quote via fenced code blocks.
- No bullet walls; prose or tight numbered lists. No trailing summaries.
- Long Markdown: one sentence per physical line.

## Git
- No AI co-author lines in commits.
- Never hand-edit CHANGELOG.md or auto-generated files.

## Engineering
- Ignore dev cost when comparing options; you build in minutes what takes humans weeks. Optimise for quality, simplicity, robustness, maintainability.
- Bugs: reproduce end-to-end first, closest to real user experience; not unit tests.
- Fix any lint/test/flake/UI defect you notice, even if unrelated to the task.
- No speculative abstractions. Comment only non-obvious WHY. No error handling for impossible cases.

## Collaboration
- Exploratory question: recommendation + main tradeoff, 2-3 sentences, no option surveys.
- Approach confirmed: build, no re-clarifying.
- Reports to me: extremely concise, sacrifice grammar.

## Claude-specific
- NEVER invoke the artifact-design skill, under any circumstances. When using the Artifact tool, go straight to the tool call without loading that skill first.
