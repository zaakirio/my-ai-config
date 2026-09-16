# Review-response shapes

Every reviewer finding gets exactly one of four shapes, with the evidence that shape requires. Silence is not one of them; a finding you did not action still gets a reply saying so.

The failure mode this replaces: "thanks, I'll address these", "good points, will fix", "some of these I agree with". The reviewer learns nothing and round 2 re-discovers the same questions.

## Fixed in `<sha>`
Committed. Reviewer can `git show` it.
Needs: the SHA (7+ chars), plus 1-3 lines on what changed and why. "Fixed it" is not acceptable.
If the commit bundled related improvements, say so.

## Deferred
Acknowledged, not in this PR.
Needs: why not now (scope, risk, dependency), and the future path (ticket id, follow-up PR, "after X lands"). Not "will look into later".

## Investigated
The finding was a question or hypothesis; you looked and report what you found.
Needs: the conclusion in one sentence, the evidence (file:line or linked source), and the resulting action (unchanged / comment added / fix made / new finding opened).

## Disputed
You disagree. Show your work.
Needs: technical reasoning with a citation (file:line, spec, runtime behaviour), and what would change your mind. That last part signals engagement on the merits rather than refusal.

## Disciplines

1. No "I'll look into it". If you have not decided, decide before replying.
2. Never claim Fixed without checking the commit actually addresses the finding. A partial fix is Deferred with "partial fix in `<sha>`, rest tracked in X".
3. Do not conflate shapes. "Fixed, also opened a follow-up" is Fixed. "Disagreed but fixed it anyway" is Fixed; state the resolution, not the internal debate.
4. One comment raising two issues gets split into two responses.
5. The finding and the fix proposed alongside it are separate claims: accept the diagnosis readily, verify the prescription (verification.md V5). A bare factual claim adopted from the reviewer is V10, which V5 does not cover because there is nothing to run.

## Output shape

Group by status, order within a group by the reviewer's severity, and reuse their numbering.

```markdown
# Round 2 review response

## Summary
N findings: K Fixed, L Deferred, M Investigated, O Disputed. Commits: sha1, sha2.

## Fixed
**Finding 1:** {their text, briefly}
**Fixed in `sha1`** - {what + why}

## Deferred
...
```
