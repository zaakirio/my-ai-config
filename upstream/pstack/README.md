# Lauren's pstack source record

Author: [Lauren Tan, poteto](https://github.com/poteto).
Upstream: [cursor/plugins/pstack](https://github.com/cursor/plugins/tree/main/pstack).
This bundle uses no third-party port.
The exact reviewed revision and per-file SHA-256 hashes are in [manifest.json](manifest.json).
The unchanged selected originals are under `source/`; they are reference data, not installed skills.
The original [MIT licence](source/LICENSE) applies to those files and their adapted portions in this bundle.

| Local workflow | Upstream source |
| --- | --- |
| `zk-correct` | `correct` |
| `zk-blast-radius` | `blast-radius` |
| `zk-perf` | `benchmark-checklist`, Hillclimb |
| `zk-create-verifier` | `create-verification-skill`, Build the Lever |
| `zk-maintain-verifier` | `maintain-verification-skill` |
| Project delivery evidence | `show-me-your-work`, Build the Lever |

Run `python3 scripts/check-upstream.py --offline` to check the retained originals.
Run `python3 scripts/check-upstream.py` to compare those same files at upstream's current `main`.
Exit 0 means unchanged selected files, 1 means review needed, and 2 means the check failed.
Unselected upstream files are outside this check's coverage.
The command never updates the pin, installs code or follows a third-party repository.
Review a reported change against local use, update the adaptation if useful, then refresh the retained file, revision and hash together in a normal reviewed change.
Do not replace local authorization, model choices, CI policy or project acceptance with upstream defaults.
