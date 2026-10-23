# Concurrency and lifecycle

Read when changing concurrency, task ownership, cancellation, or shutdown. Choose concurrency for a required workload, not because code performs I/O. Sequential sync code is valid. Preserve existing call paths unless migration is requested.

## Execution model

- Use asyncio for overlapping I/O with compatible libraries; never block its event loop. Synchronous database drivers and file I/O block too, including lock and busy waits: run them in threads or keep them provably short. Offload blocking calls to bounded threads. Cancelling the await does not stop a running thread: its work needs its own timeout or cooperative stop contract.
- CPU work may use processes, native code releasing the GIL, or compatible free-threaded/interpreter-pool execution. Benchmark serialization, startup, memory, and contention; verify extension-module support. Do not assume async computation runs in parallel.
- Libraries do not call asyncio.run; the application owns loop startup. Frameworks may own it. Avoid forced sync/async twins and hidden loop nesting.

## Ownership and bounds

Every task has an owner that retains, awaits, and accounts for it. Prefer TaskGroup when sibling failure should cancel the group; use an explicit partial-failure policy otherwise. Handle ExceptionGroup members without hiding unrelated failures.

Bound active operations, queued input, and task creation. A semaphore around work does not bound a task-per-item allocation. Apply backpressure with bounded queues or worker pools; define overflow and fairness when relevant. Propagate an end-to-end deadline instead of resetting the full timeout at each nested call.

## Cancellation and shutdown

- Preserve CancelledError. Use finally and context managers for cleanup; cancellation may arrive after a side effect succeeded but before acknowledgement.
- A timeout is not cancellation shielding. When cleanup must survive caller cancellation, retain the cleanup task, shield its await as needed, and have an owner await completion with a bounded shutdown policy. Shield alone neither waits for completion nor prevents process termination.
- Stop accepting work, drain or cancel within a deadline, await owned tasks, then close shared resources. Partial startup follows the same ownership rules. Do not cancel a resource owner while its workers still depend on it.
- For queues, define acknowledgement and unfinished-work accounting. Queue.shutdown on supported versions helps termination; immediate shutdown does not prove work completed. Support platform-appropriate signals and service stop hooks.
- Async subprocess timeout requires termination, escalation if needed, and reaping; cancellation of a wait is insufficient.

## Shared state and processes

State read before an await is stale after it: re-read, or write conditionally (`WHERE status = ?`, a version column) so a concurrent writer's change is not overwritten. State single-instance assumptions (one process, one background loop) and enforce them with a lock or startup check; extra workers or replicas duplicate loops and effects. Protect multi-step invariants, not individual dict operations. The GIL is not a transaction or a portability guarantee. Keep lock scope explicit; use the lock type appropriate to threads or tasks and a consistent acquisition order. Avoid holding locks during external waits unless required by the protocol.

Use ContextVar for request context, not shared mutable globals. Create clients, connections, and locks in their owning execution context. Process workers accept picklable data, not live resources; choose a compatible start method explicitly at application boundaries and allow callers to supply context. Interpreter isolation and free-threaded execution require distinct safety checks.

## Checklist

- [ ] Execution model serves the workload; event-loop blocking and allocation are bounded.
- [ ] Every task and resource has an owner, deadline, and shutdown path.
- [ ] Tests exercise failure, cancellation, cleanup, and concurrency limits using synchronization rather than sleeps.
- [ ] Background thread/process effects and shared-state invariants remain safe after cancellation.
- [ ] No write is based on state read before an await; single-instance assumptions are enforced.
