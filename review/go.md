# Go patterns

Shapes that recur in Go diffs. Scan for each; cite the code (GO4 at `file:line`).

Principle: Go's costs are explicitness costs. The bugs are in what the explicitness hides: an error swallowed on purpose, a goroutine nobody waits for, a channel with no exit.

## GO1 Error dropped on the floor
`x, _ := f()`, `_ = g()`. Occasionally deliberate; always a claim that the error is worthless. It usually is not.
Fix: handle it, or a comment saying why this specific error cannot matter.

## GO2 `%v` breaking the chain
`fmt.Errorf("failed: %v", err)` formats the error away. `errors.Is` and `errors.As` above the call site now see nothing.
Fix: `%w`, or return the sentinel unwrapped when the context adds nothing.

## GO3 `==` on a wrapped error
Comparing a wrapped error with `==` or a type assertion instead of `errors.Is` / `errors.As`. Breaks the day anyone adds context between.
Fix: `errors.Is` / `errors.As`, always, once wrapping exists anywhere in the stack.

## GO4 Goroutine with no exit
`go func()` that blocks on a channel the sender abandoned, a ticker nobody stops, a context it ignores. Leaks silently; a hundred requests later the process is slow and nobody knows why.
Fix: select on `ctx.Done()`, `defer wg.Done()`, stop the ticker, close from the sender side only.

## GO5 Loop variable capture
`for _, v := range xs { go func() { use(v) }() }`. Fixed in Go 1.22; alive and biting on anything older. Check `go.mod` before judging.
Fix: pass `v` as a parameter, or upgrade the toolchain.

## GO6 `defer` inside a loop
Defers run at function return, not iteration end. A loop opening files or connections holds every one of them until the caller finishes.
Fix: extract the body into a function, or close explicitly.

## GO7 Nil map write
`var m map[string]int; m[k] = v` panics. Reads from nil maps are fine, which is why this hides.
Fix: initialise at declaration; flag any write path a constructor does not cover.

## GO8 Mixed receivers
Some methods on `T`, some on `*T`, one type. Mutation works through half the API and silently does not through the other.
Fix: pointer receivers for anything that mutates or is large; pick one and hold it.

## GO9 Context stored or dropped
`context.Background()` deep in a call stack, a ctx field on a struct, a request-scoped deadline discarded. Cancellation and tracing stop at the seam.
Fix: pass ctx as the first parameter, end to end.

## GO10 Shared map or slice across goroutines
Writes racing reads, no mutex, no channel ownership. Tests pass; production corrupts. If the diff adds concurrency, ask what runs under `-race`.
Fix: a mutex with a small critical section, or hand ownership through a channel.

## GO11 Body or rows never closed
`resp, err := http.Get(...)` without `defer resp.Body.Close()`; `rows, err := db.Query(...)` likewise. Connection pools drain quietly.
Fix: defer the close on the error-free path, immediately after the check.

## GO12 Closing from the wrong side
A receiver closing a channel, or two senders where either might close. Panic on the second send-after-close.
Fix: only the sender closes; multiple senders mean a `sync.Once` or a dedicated quit channel.

## GO13 Shadowed `err` in a nested block
`if err := f(); err != nil { ... }` checks the inner one while the outer `err` stays nil, or the reverse: an inner `:=` shadows and the deferred cleanup reads the wrong variable.
Fix: name the inner one differently, or hoist the declaration.

## GO14 `time.After` in a loop
Each iteration leaks a timer until it fires. In a hot retry or select loop this is real memory.
Fix: a `time.NewTimer` reused with `Reset`, or a `Ticker` that gets stopped.

## Do not raise

Interface size debates when the interface has two consumers and both use it. `gofmt` and import order; the linter owns those. Constructor naming taste. Error message capitalisation unless the project has a visible convention the diff breaks.
