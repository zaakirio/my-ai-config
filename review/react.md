# React patterns

Shapes that recur in React and Next.js diffs. Scan for each; cite the code (RE3 at `file:line`).

Principle: React's bugs are timing bugs. State, effects, and renders disagree about what moment it is. Every finding below is a way those clocks drift apart.

## RE1 Effect computing derived state
`useEffect(() => setFullName(first + ' ' + last), [first, last])`. A render behind, a state variable that cannot disagree with its inputs but now can.
Fix: compute during render; `useMemo` only if the computation is genuinely expensive.

## RE2 Effect with lying dependencies
A dep array missing values the effect reads, or an `eslint-disable react-hooks/exhaustive-deps` comment. The disable is the confession: the effect runs on a clock the author chose, not the data's.
Fix: put the real deps in, or restructure so the effect does not read changing values (refs, functional updates, moving the logic out).

## RE3 Missing cleanup
Subscriptions, timers, listeners, sockets opened in an effect with no cleanup function. Remount doubles them; unmount leaks them.
Fix: return the cleanup; if the effect sets up, it tears down.

## RE4 Fetch effect without cancellation
`useEffect(() => { fetch(...).then(setData) }, [id])`. Flip `id` fast and the slow response wins: stale data rendered as current.
Fix: an `AbortController` or an ignore flag in cleanup, or move fetching to the query layer.

## RE5 Index keys on a reorderable list
`key={index}` where items can reorder, insert, or delete. React reuses the wrong component state: a checkbox, a draft input, an animation belongs to a different row now.
Fix: a stable id. If the list can never reorder, say so in a comment and move on.

## RE6 Stale closure over state
A callback, timeout, or subscription reading `count` from the render that created it. The value is frozen; the bug appears exactly when updates get rapid.
Fix: functional `setState(c => ...)`, or a ref for values the callback must read fresh.

## RE7 setState during render
A state update called unconditionally in the render body. Infinite loop, or a render loop that "works" because a condition happens to bound it.
Fix: derive the value, or move the update into an event or effect.

## RE8 Props duplicated into state
`useState(props.initial)` where the prop is the live source of truth. The copy diverges on the next prop change, and somebody adds a sync effect (RE1) to paper over it.
Fix: one source of truth. If the component genuinely owns a draft, name it as one and define when the prop wins.

## RE9 Context value with unstable identity
`<Ctx.Provider value={{ a, b }}>` re-creates the object every render, re-rendering every consumer every time. Invisible until the tree is big; then it is the whole profile.
Fix: memoize the value, split the context by change frequency.

## RE10 Premature memoization
`useMemo` and `useCallback` wrapping values nothing memoizes downstream: no `React.memo` child, no dep array depending on the reference. Cost paid, nothing bought.
Fix: delete it. Memoize when a measured re-render or a referential-equality contract demands it, and cite which in the finding.

## RE11 'use client' creeping upward
The directive on a layout or a page that only needs one interactive leaf. Everything below it ships to the browser now, server components included.
Fix: push the boundary down to the actual interactive component.

## RE12 Server-to-client function props
Passing a function from a server component into a client one (other than server actions with the directive). It cannot serialize; it fails at the boundary or silently changes behavior.
Fix: a server action, or restructure so the interactivity owns its own handlers.

## RE13 Missing Suspense or error boundary around async UI
`lazy()`, a data-fetching hook that suspends, or React 19 `use()` with no boundary above it. One rejection unmounts the whole tree.
Fix: boundary at the level where the fallback UI makes sense, and name what the user sees while pending and on error.

## RE14 Optimistic update without rollback
`useOptimistic` or a query-cache write that assumes success, with no revert path on rejection. The UI lies until the next refetch.
Fix: the rollback path is part of the feature; if it is missing, that is the finding.

## RE15 dangerouslySetInnerHTML without sanitization
Cross-reference `reference/xss-prevention.md`. Framework escaping was the safety net; this line cut the net.
Fix: sanitize, or render structured content instead of HTML.

## Do not raise

Hook naming and component structure taste. Class-versus-function anything. Memoization on a list of ten items. Form library preferences the project already settled. React's idioms change yearly; flag what breaks behavior, not what a newer version would write differently.
