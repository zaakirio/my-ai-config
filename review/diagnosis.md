# Diagnosing a defect

Read before scoping a reported bug, before judging a PR that claims to fix one, and before acting on someone else's diagnosis.

## Establish the observed behaviour first

Start from the end user's experience, not an error string or an implementation hypothesis. Reproduce end to end along the real user path. If a faithful reproduction is not feasible, record the exact limitation and use the closest path without presenting it as equivalent evidence.
Capture expected behaviour, observed behaviour, setup, inputs and repeatability before assigning a cause.

## Keep three facts apart

- **Initiating trigger**: the event, input or transition that starts the faulty behaviour.
- **Masking condition**: the independent state, timing, cache, config or path difference that hides or exposes it.
- **Visible symptom**: what the user or operator can actually observe.

Do not collapse them into one label. A masking condition explains why a fault appears only sometimes without being the cause, and the symptom is often several layers downstream of both. Most wrong fixes are a masking condition mistaken for a trigger.

## Test the causal explanation

Inspect the failing path beside a proven path where the behaviour is known to work, and find the earliest meaningful divergence in inputs, state, dependencies, timing or control flow.
Read history (blame, commits, migrations, prior implementations) when it explains why the paths diverged or which invariant was intended. The most recent nearby change is not causal without evidence.
Name the smallest counterfactual that should change the outcome if your explanation holds, change one condition at a time, and record whether the symptom appears, disappears or is unchanged.
Seek disconfirming evidence deliberately: state what observation would falsify the explanation, run that check, and keep contradictory results rather than explaining them away.
The final explanation must account for both the failure and the success of the proven path.

## Reviewing a fix

Verify the claimed cause explains the end-user reproduction and the proven path without leaning on an untested masking condition. A fix resting on one is a fix that will come back under a different condition.
Ask for the reproduction, the trigger/mask/symptom separation, the divergence, the counterfactual, and the disconfirming check. If a load-bearing one is missing, say which, rather than treating confidence or implementation detail as proof.
The reproduction should have become the regression test. A fix with no test that fails without it has not been shown to fix anything (verification.md V8).

## Acting on someone else's diagnosis

A diagnosis, report or implementation-ready recommendation is evidence, not authorisation to change code. Adopting its factual claims makes them yours (verification.md V10) and adopting its prescription is a separate claim again (V5).
