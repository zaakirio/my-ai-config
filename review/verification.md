# Verification

Iron law: evidence before assertion. Run the check, read the source, then claim.

Binds three roles:
- reviewing: your findings and your suggested fixes are claims (V1, V5-V10)
- authoring: your comments, docstrings and PR prose are claims (V1-V4, V6, V10)
- responding: what you adopt from a reviewer becomes yours (V5, V10)

Each lesson below came from a real failure. Run the check when its trigger fires.

## V1 Load-bearing claims need cited evidence

Trigger: you asserted how a library, ORM, DB, sibling file or topology behaves.

Cite file:line, grep output, EXPLAIN output, an official docs URL, or a reproducible step.
"The name suggests", "architecturally it must", "I'm fairly sure" are not evidence.
Decompose multi-hop claims ("A calls B, which feeds C") and cite per hop, or state which hops are unverified; verifying hop 1 and completing the chain from recall reads as uniformly backed while resting on nothing.
Anything sourced from memory or a previous session's notes is unverified by default: refactors invalidate notes silently and leave them looking authoritative.
Verify arithmetic asserted in prose by computing it.
A guard that checks a view entity's property is not checking the base-table column.

## V2 Re-audit the pattern after fixing one instance

Trigger: the diff fixes a class of issue, not a single site.

Grep for siblings at B, C, D. Fix them here if cheap, else record an explicit tracked deferral.
Sweep on the defect's semantics, not one greppable handle: identifier, structural position and guard shape each miss a different sibling. Use two and cross-check.
A declaration one level up is invisible to a search at the site (container annotation covering members, base type its subtypes inherit, module-level marking). Treat any "these N are all of them" resting on a flat search as a lower bound until inheritance, composition and container-level application are checked.
When collapsing sweep results (dedupe, sort -u, a table), check the dropped field was not the discriminator.
A new throw/panic/raise can be right in isolation and wrong in context: if it lands inside an existing catch, that catch may swallow it and skip error-counting or escalation.
Mirroring a hardened sibling onto a new site: diff the two bodies, not just their guard structure, and copy from the hardened one.

## V3 Prose must match control flow

Trigger: a PR body, commit message or design doc narrates conditional logic or a contract.

Grep each described branch in the implementation after writing it. A body describing logic the code lacks misleads as much as a code bug.
A JOIN or GROUP BY change can alter response shape or status code (an absent row that returned 404 now returns a zero-valued 200). Never call an INNER/LEFT switch a no-op without proving row-set equivalence.

## V4 Headers update with semantics, and prose lands last

Trigger: behaviour changed in a way that contradicts the file's header docstring.

Re-read and update the header in the same commit.
Ordering is load-bearing: land behaviour first, prose last. A docs pass that runs first gets falsified by the code landing after it, and nothing catches that. Line references, symbol names inside comment text and English claims are invisible to the compiler, to lint and to every test.

## V5 A suggested fix is a second, separate claim

Trigger: a finding arrives with a concrete fix and you are about to adopt it, or you are about to offer one.

The finding's validity does not transfer to the fix. A valid finding with a wrong fix is worse than an unaddressed finding: an open comment stays visible, an adopted-but-wrong fix reads as resolved to everyone downstream.
Reviewers see the diff, not the runtime. Accept the diagnosis freely; verify the prescription always.
1. State what the fix changes about behaviour, not what the finding was.
2. Enumerate the inputs whose handling changes and check against real ones. Run it, do not reason about it.
3. Be most careful with fixes that tighten something (validator, guard, allowlist, type) or narrow a broadcast to a subset. Both move cases into a new branch, and the cases newly landing there are exactly the ones nobody enumerated.
4. Grep every call site flowing through the changed path.
5. Establish what happens downstream of a new rejection. On an unattended path the symptom of a throwing validator is silence, not an error.

Observed: a proposal to gate a cluster-wide broadcast on "does this pod hold the socket" would have delivered every message twice, because the guard did not stop the fan-out. Another proposed banning a bare token the codebase legitimately needed once, reddening the build. Both diagnoses were right; neither prescription was checked.

## V6 Re-fetch before asserting remote state

Trigger: any claim about the current state of something you do not own locally. A branch HEAD, a version pinned elsewhere, mergeability, which tags exist, what is deployed.

Read only from refs you fetched this turn, and check the fetch exit code explicitly. Do not pipe it through head/grep and lose the status; do not infer success from empty output. A failed fetch leaves the old refs in place and stale refs are indistinguishable from fresh ones at the point of use.
A failed fetch means fix the access path and re-fetch, not fall back to the local ref with a hedge. A remote's configured protocol is not proof of the working access path: origin may be SSH while your credential is an HTTPS API token.
If no access path works, stop and report the inability. This is the terminal branch and it is not optional. It outranks any graceful-degradation rule: degrade the review, never the freshness of a claim you publish.
When two reads of the same state disagree, do not average them or take the convenient one. Find a third read structurally closer to the source. Observed: a PR-summary endpoint served a stale head SHA while the workflow-runs endpoint already reported runs six commits later; the PR object plus a forced ref fetch agreed with each other and arbitrated.
Compare with three dots: `origin/<base>...origin/<head>`, which diffs from the merge base as the host does. Two dots against a moving base silently attributes other people's merged commits to the PR, and degrades gradually so the output stays plausible while getting wronger. Compare against the fetched remote base, never a local default branch: a pooled or long-lived clone does not keep its local default current, and a recorded head SHA never wins over a reachable remote one.
Withdraw the downstream conclusion when a stale read surfaces, not just the number.

## V7 Confirm the instrument can observe the subject

Trigger: you cite a metric, dashboard, health check, log query or monitor as evidence. Especially a null result ("no errors", "lag normal", "nothing changed").

Write in one sentence what the instrument measures: subject, scope, aggregation. Compare to the claim. If the claim's subject is not the instrument's subject, the measurement is not evidence however healthy it looks.
Distinct from V6: V6 is stale input, right instrument. V7 is fresh input, wrong instrument. Neither shows as an anomaly.
Be most suspicious of instruments reporting on "the current/latest/active" instance; those definitions routinely exclude the instance you care about.
For a null result, describe what a positive would have looked like. If you cannot, you can conclude nothing from its absence.
When a monitor alarms across an unexpectedly broad population, check for implausibly uniform values first. Uniformity pinned at a boundary (0, null, a maximum) points at the apparatus; genuine scatter points at the thing measured.
In a diff: a metric label no code path can emit yields a permanently empty series that reads identically to healthy. Deleting the branch that produced a label makes that label's documentation a claim about an instrument that cannot fire.
State the instrument alongside the claim so a reader can challenge the choice of instrument.

## V8 A mutation test proves only what it mutated

Trigger: you broke something on purpose to prove a test is load-bearing and cite the failures as evidence.

Mutate one component at a time. Emptying the whole list, `if (false)`, deleting the entire guard prove something is covered, never that each part is.
The mutated program must pass the gates CI runs. If you needed a cast or a suppression to make it run, you measured a program the pipeline would reject; where typecheck is a gate, the compile error is itself the guard.
Record which tests failed, not how many. "N tests failed" without names is an unverified claim about which behaviour is guarded.
For a test you are adding, confirm it fails in isolation under the mutation it targets.
Prefer the mutation a plausible future change would make (wrong-sibling swap, dropped dependency, inverted comparison) over the maximal break.
A mutation that stays green is the finding. Report it rather than reaching for a bigger break.

## V9 Prove the check can fail before trusting that it passed

Trigger: a clean result is cited as evidence. A search finding nothing, a query with no rows, a suite with no failures, an empty diff, a revert producing no change.

A check structurally incapable of reporting failure emits exactly the same output as a genuine pass. Most dangerous of V7/V8/V9 because the clean result arrives because you were verifying, and reads as the reward for it.
1. Make it non-clean once: relax the filter, widen the range, drop the most specific predicate, point it at a case that must fail.
2. Check exit-status propagation. A shell pipeline reports the last stage's status, so a producer's "found nothing" is masked by any formatting stage after it.
3. Confirm what you removed was actually removed. A revert or substitution that silently no-ops leaves the original state intact.
4. Confirm field and key names against live data. A filter naming an absent or misspelled field returns zero rows, indistinguishable from no matches.
5. State the falsifying case alongside the clean result.

A skipped step is not a passed step. In a sequential job where one failure aborts the rest, later steps report "skipped", which renders identically to failed on a summary view. A newly added step is always last and so is the most likely never to have run. Confirm a gate executed before citing it as coverage.
Report a broken check rather than quietly redoing it: discovering a verification could not have failed is itself a finding about what the earlier conclusion was worth.
Two checks passing for different reasons are not corroboration; confirm they can fail independently.
Suspect a clean result that arrived faster or more easily than expected. Absence of friction is usually absence of work.

## V10 A claim you adopt becomes your claim

Trigger: you write into code, a comment, a PR body or a review response an assertion whose source is someone else. A reviewer, a ticket, a design doc, another agent's report, an earlier session's notes.

Provenance is not verification. An inherited claim feels pre-checked, which is exactly why it skips the check a self-authored claim would get.
Distinct from V5: V5 adopts a fix, which has inputs you can run against. V10 adopts a bare factual assertion, which has nothing to run, so V5's machinery does not apply.
1. Mark which assertions came from someone else.
2. Verify each at V1's standard.
3. If you cannot verify it, attribute it ("per the review", "per TICKET-123") rather than asserting it.
4. When an inherited claim turns out wrong, say where it came from. That is what stops it being re-adopted from the same source.

Observed: a review asserted a database lock-conflict matrix, the author transplanted the wording into a migration comment unchecked, and one row was wrong. Nobody had ever verified it; the review's authority did all the work. Same PR: a review stated "all four new test surfaces genuinely execute", the author repeated it, and one had never executed once.

## The `(unverified)` token

One contract, used by every agent that produces findings and by the orchestrator that consumes them.

Use the exact token `(unverified)`, never a prose variant, so it can be matched on.
It is legitimate in three cases only: the behaviour is runtime-only and cannot be read from source, the dependency is absent from the tree you were given, or you were told there is no PR-head tree. State which one applies.
Anything a grep or a Read would settle in the tree you were given may not be labelled. A reviewer holding Read, Grep, Glob and Bash on a correct tree has an honest set close to empty.
The orchestrator resolves every labelled finding against the tree, demotes what is still unresolved below critical with a statement of what could not be checked, and counts them in the summary. The label costs a reader's trust; it does not buy an exemption, and it never survives into an approve.
