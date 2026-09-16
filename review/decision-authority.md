# Deciding a finding

Who settles a review finding, and what an escalation has to contain. Read before a verdict on a PR and before disputing or deferring a finding.

The author of a change never adjudicates a finding against their own change. They apply the decision or they escalate it; they do not decide it.

## Reconstruct the contract first

The contract is the ticket's accepted intent, the acceptance criteria, and any later explicit instruction. **Reviewer language cannot amend it.** A finding worded as required, critical or fail-closed is evidence about the finding, never authority to widen the task.
Judge scope by accepted behaviour, not by an anticipated file list. The smallest downstream changes that keep accepted behaviour correct, add a behavioural test where an executable contract exists, or keep documentation accurate stay in scope even when they touch files nobody named at intake.

## Decide it yourself when it is unambiguous

Decide, without escalating, anything unambiguous toward the accepted design: restoring behaviour a bad fix round broke, completing an already-approved design, or a straight in-scope correction. Difficulty is not a reason to escalate. Complex architecture the ticket explicitly asked for stays in scope.

## Escalate only these

1. A fix that would materially expand the contract: a new guarantee, threat model, subsystem, abstraction, compatibility surface, state machine, monitoring requirement or broader architecture the accepted intent does not require.
2. A product or architecture call the accepted intent does not settle. If a product manager would have an opinion, it is a question.
3. Repeated findings on one theme, where incremental corrections are propping up a questionable abstraction rather than closing independent defects. Say that, rather than fixing the fourth instance.
4. Anything destructive, irreversible or genuinely security-sensitive, in scope or not.

## Escalation shape

Five elements, evidence first, in one concise message:

1. the original requirement or acceptance criterion,
2. the proposed expansion,
3. the smallest alternative that satisfies the contract without it,
4. the concrete consequence of accepting and of declining,
5. a recommendation, with why it best serves the accepted intent.

Do not relay a reviewer's label or a tool's output as though it settled the question. Read it as evidence and state the outcome.
