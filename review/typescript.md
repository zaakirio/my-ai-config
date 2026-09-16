# TypeScript patterns

Shapes that recur in TypeScript and JavaScript diffs. Scan for each; cite the code (TS4 at `file:line`).

Principle: the compiler is the first reviewer. A type that lies is worse than no type, because everything downstream trusts it.

## TS1 `as` narrowing without evidence
`value as string[]` where the runtime value is `string | string[]`. The cast silences the checker; it does not change the value. Worst at trust boundaries: API responses, `JSON.parse`, message payloads.
Fix: `unknown` plus a type guard, or a validator at the boundary.

## TS2 Double cast through `unknown`
`x as unknown as T` is the author telling you the types do not line up. Occasionally forced by a library's lies; usually hiding a shape mismatch that will bite at runtime.
Fix: name the actual mismatch in a comment if it is truly forced, else fix the types.

## TS3 Non-null assertion on a reachable null
`user!.email` where the null path exists upstream: an optional chain, a find that can miss, a ref before mount. Each `!` is a claim; check the claim.
Fix: handle the null, or restructure so the compiler can see it is gone.

## TS4 `JSON.parse` and friends returning `any`
`JSON.parse`, `req.body`, `localStorage.getItem` results flow into typed code unchecked. The type system is blind from that point on.
Fix: parse into `unknown` and validate, or a schema library at the boundary.

## TS5 Floating promises
An async call with no `await`, no `void`, no `.catch`: fire-and-forget by accident. Rejections become unhandled, ordering becomes luck. Cross-reference S9 when the float happens after a response is sent.
Fix: await it, or `void` it with a comment and its own error handling.

## TS6 Async function in a void callback
`onClick={async () => ...}`, `setTimeout(async ...)`. Rejections have nowhere to go; the framework cannot catch them.
Fix: wrap the body in try/catch with a real error path, or route through something that handles rejection.

## TS7 `Object.keys` / `Object.entries` lying about keys
They return `string[]`, so code iterates keys the type says cannot exist, or misses ones it says must. `Record<K, V>` from parsed input is the same lie one step earlier.
Fix: validate the key set, or type the loop explicitly and handle unknown keys.

## TS8 Numeric enum from the backend treated as exhaustive
Numeric enums accept any number at the type level's edges, and a new backend state arrives as a value the switch never saw. Cross-reference S6 and S10.
Fix: a union of string literals where you control the contract, an exhaustiveness check where you do not.

## TS9 New `@ts-ignore` / `@ts-expect-error` without the why
Each one disables the reviewer that never sleeps. Sometimes right; always load-bearing.
Fix: a comment naming what is wrong upstream, and prefer `@ts-expect-error` so removal gets flagged.

## TS10 Optional chaining hiding an impossible state
`data?.items?.map(...)` where `data` being absent is itself the bug. Renders empty, looks calm, reports nothing. Cross-reference S1 and S2.
Fix: make absence explicit at the boundary and handle it there.

## TS11 `any` leaking in through a library
A dependency's `any` return, an untyped module, a `declare module` stub. The diff inherits the lie by calling it.
Fix: a local wrapper with an honest signature beats sprinkling casts at every call site.

## TS12 `satisfies` where annotation was meant, and vice versa
Annotation widens and loses the literal; `satisfies` keeps it but does not check the use site. Picking the wrong one either erases information or fails to constrain.
Fix: `satisfies` to validate a literal-shaped value, annotation when the wider type is the contract.

## Do not raise

Stylistic generic gymnastics. `readonly` evangelism on types nothing mutates. `unknown` over `any` in positions where the value is checked one line later. A cast in a test fixture. The type system's austerity budget is spent at boundaries; do not spend it on interiors.
