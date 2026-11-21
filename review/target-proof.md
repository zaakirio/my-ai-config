# Prove the target the user asked for

## A changed screen

Before editing, identify the approved reference and the exact state that may change.
Record route, viewport or device, theme, data and interaction state; capture the same state after the edit.
For reproduction, use the project's existing tolerance and keep the reference fixed.
For a redesign, label what should differ and show the pair on first handback.
No approved reference means you can show a change, but cannot claim parity.
Keep the compact pair after cleanup.

| Project | Use | Limit of the claim |
|---|---|---|
| LingoBite | Run `node scripts/design-parity.mjs <screen>` for design-board frame fidelity, after the design build required by the project. For an approved mock or recording, compare the actual app state with that separate reference. | Board and app can be equally wrong. Phone-width web does not prove native UI. |
| Meadow Study | Use the affected journey from `docs/verification.md`, with its fixture and viewport. For a changed accepted visual state, show just that state beside its approved reference. | Game concepts and historical source art do not establish implementation. Keep the accepted style closed; no game-wide pixel-equality gate. |

## A requested release

Use the existing deployment verifier and its authoritative build ID, then exercise one discriminating user action on the named target.
Report `target | expected revision/build | observed revision/build | action → observed result | proof or gap`.
A stale build can pass a smoke test; an exact build can still fail the action.
Neither alone proves the request.

For LingoBite, use the project's delivery verifier for `dev`, `main` or the design site as applicable.
A fixture-site pass is not a production API pass.
For TestFlight, identify the build available on that channel and distinguish that from a device run on that build.
For analytics, trigger the event on the target and confirm its arrival in the intended analytics project with a matching test identifier or timestamp.
If target access, receipt or build identity is missing, report exactly which observation is unavailable.

## Check the pilot

For the next five eligible visual handbacks and five release handbacks, record the first result in existing project notes: `case | target proved? | mismatch caught | extra turns for missing proof | minutes collecting proof`.
Compare with five similar prior cases per recipe; mark missing historical time unknown.
Exclude scope changes and new design preferences.
Keep the check if it finds a real mismatch or reduces evidence requests at a reasonable cost.
