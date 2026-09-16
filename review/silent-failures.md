# Silent failure patterns

Shapes that recur in AI-assisted and hand-written backend work. Scan the diff for each; cite the code (S6 at `file:line`) so the author can look up the fix shape here.

Principles: an error without logging and user feedback is a defect. Fallbacks must be explicit and justified. Catch blocks must be narrow. Mocks and stubs belong in tests only.

## S1 `?? CONSTANT` on a DB-projected field
`row.field ?? Enum.DEFAULT`. Hides two bugs at once: column missing because the pod started before the migration, and a refactor dropping the column from the projection. Both surface as "everyone gets the default".
Fix: make the field nullable and handle absence, or log when the fallback fires.

## S2 One return value for two different conditions
`return null` for both "no row yet" (benign) and "schema drift" (bug). The caller cannot tell them apart, and a debug-level log on the benign path hides the other. Worst inside a monitor or health check.
Fix: separate sentinels, throw on the error case, or a discriminated union.

## S3 "Skip emission" implemented by emitting a sentinel
AC says skip/omit/do not emit; code calls `metric.emit(NaN)` and relies on one downstream exporter dropping it. Other consumers plot it, and NaN can break JSON marshalling for the whole batch.
Fix: early return before the emission call.

## S4 INNER to LEFT JOIN claimed as a no-op
Changing JOIN kind changes which rows survive: orphan and race-window rows reappear, and LEFT + GROUP BY turns 404-on-empty into 200-with-zero. Never a no-op.
Fix: a test capturing the row-set difference, or an explicit note that the contract changed.

## S5 Catch block whose first statement throws
`catch (e) { throw new Other(e.message) }`. The catch exists nominally, escapes immediately, and drops the original stack unless `cause` is set.
Fix: remove the catch and let it propagate, or add real handling.

## S6 Predicate inversion on a multi-state enum
`if (status !== 'active')` assumes two states; the type has `pending | failed | stuck | queued`. Read the enum definition before trusting the negation.
Fix: whitelist the intended values, or switch.

## S7 Two-phase recovery clearing only some sentinel fields
Write sets `proposed_at` + `proposed_tx_hash` + `proposed_value`; the failure handler clears one. Retries then hit a "we already have a hash" guard and skip forever.
Fix: define the field set once and have both write and recovery iterate it.

## S8 Mark-then-persist
`entity.status = 'PROCESSED'; await repo.save(entity)`. If the save throws, the in-memory entity still reads as processed and downstream behaves as if it were.
Fix: persist then mark, or a transaction with rollback semantics.

## S9 Fire-and-forget after the response has been sent
Work started after `res.json(...)` runs outside the request lifecycle, so the framework's global exception filter no longer covers it. Unhandled rejection goes nowhere.
Fix: await before responding, or enqueue onto a job system with its own error handling.

## S10 Non-exhaustive switch on a tagged union
Missing case returns `undefined` implicitly; a variant added later falls through silently.
Fix: `default: const _exhaustive: never = kind` so the compiler flags new variants.

## S11 Read-then-delete on shared state
`SMEMBERS` then `DEL` loses any concurrent `SADD` in between.
Fix: `SPOP key count`, or MULTI/EXEC.

## S12 Fail-open applied to a write
Fail-open on a cache read is fine (skip cache, hit the DB). Fail-open on a cache, queue or notification write silently reintroduces the problem the write existed to prevent.
Fix: log and escalate on write failure even where read failure is tolerable.

## S13 `COALESCE(SUM(x), 0)` used as a presence check
0 means "never happened" and "happened, nets to zero" (refunds, reversals). Idempotency silently fails.
Fix: `COUNT(*) > 0` for presence, SUM for amount, or an explicit `claimed_at`.

## S14 NaN passes numeric thresholds
NaN is not greater than anything and not less than anything, so it escalates nothing and recovers nothing.
Fix: `Number.isFinite` guard at the entry of any exported numeric function.

## S15 In-memory state behind a distributed lock
The lock serialises across replicas; instance fields do not. N replicas give N copies of the state machine, so "consecutive samples" transitions split and never fire.
Fix: move state to shared storage, or assert single-replica in code.

## S16 Format validation mistaken for semantic validation
`/^0x[0-9a-f]{64}$/` passes `0x000...0`. The shape is right, the value is the uninitialised sentinel, and downstream treats it as real.
Fix: reject known sentinels explicitly after the format check.

## S17 Log-and-continue producing plausible-but-wrong output
`catch { return '' }` where the empty string is syntactically valid downstream. Consumers cannot distinguish "formatter failed" from "value was empty" and ship wrong content.
Fix: throw, return a tagged error, or render a visible error marker.

## S18 ORM update with an undefined field
`repo.update(id, { field: maybeUndefined })`. TypeORM omits the field from the SQL, the column keeps its old value, and the success log is a lie. Prisma and Sequelize have analogues, all differing between undefined, null and omission.
Fix: narrow before the call, or use the ORM method that errors on undefined.

## Recommend honest error paths, not speculative instrumentation

Make an existing error path honest: log it, surface it, narrow the catch, propagate it.
Do not use a finding as a lever for new dashboards, alerts or follow-up tickets against a regression there is no evidence of. If an existing safety net would catch the symptom, trust it.
Before recommending an instrument, establish the input that makes it fire (verification.md V7).
