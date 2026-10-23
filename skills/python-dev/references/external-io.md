# External I/O and persistence

Read when changing remote calls, storage, retries, transactions, or subprocesses. Keep protocol and layout knowledge localized; add wrappers or repositories when they isolate real policy, not to rename dependency methods.

## Remote calls

Reuse owned clients with connection limits, connect/read timeouts, and an end-to-end deadline; size timeouts per operation, since streaming or long-running calls need idle-based read timeouts. When relaying a response, keep forwarded headers consistent with the body you send (encoding, length, hop-by-hop). Stream and cap bodies, including decompressed size; do not trust Content-Length. Check status before decoding, parse the consumed fields into a model at the adapter (unknown fields ignored, optional where the provider varies) instead of isinstance chains at each use, and redact upstream payloads from errors. Credentialed redirects require an explicit destination policy.

Retry transient, repeatable operations only, within an attempt and time budget. Use backoff with jitter and bounded Retry-After; avoid multiplying retries across layers. Cancellation is not retryable. A generated idempotency key helps only if the receiver enforces it; reuse it for the same logical operation and define expiry and payload-conflict behavior.

A timeout leaves remote completion uncertain. Reconcile state or use a server-supported deduplication contract before repeating writes. Before a non-idempotent remote create, choose a key that makes the result findable, persist the returned id before any follow-up call, and reconcile local records by that key on timeout or restart. Decide what "not found" means on read and delete. Add outbound circuit breaking or client-side throttling for demonstrated overload/failure requirements, not by default.

## Transactions and distributed effects

- Place transaction boundaries around invariants. Use database constraints, parameterized queries, deliberate isolation, and atomic conditional updates or locking for concurrent writers. An application pre-check does not prevent races.
- Retry a transaction only when the entire unit is safe to repeat; external effects inside a retried transaction can duplicate. Coordinate durable state and external delivery with an outbox or equivalent only when atomic handoff is required.
- State delivery semantics precisely. At-least-once processing needs deduplication and safe acknowledgements; do not promise exactly-once across independent systems without an enforceable protocol.
- Long-running work started by a request (HTTP or queue) returns a job id immediately and runs as an explicit state machine (persisted status, allowed transitions, terminal states). Tasks are idempotent so redelivery or restart cannot repeat the effect, and every non-terminal state has a recovery path after restart.
- Costly or irreversible operations get limits and duplicate-submission protection.
- Prevent stale writers with version checks or fencing where leases are used. A lease timeout alone does not revoke an old worker's ability to write.
- Bound and paginate queries; avoid N+1 operations. Index every predicate and sort used on a growing table. Keep periodic maintenance off hot paths; every supported backend receives the same migrations. Test isolation, rollback, deadlocks/conflicts, and recovery against the real database. Migration rollout must account for old and new readers/writers; use staged compatibility changes when needed.

## Files and recovery

Use safe parsing, explicit encodings, validated contents, and a defined corruption policy. For atomic replacement, write a temporary file on the same filesystem and replace it after successful validation. Atomic visibility is not crash durability: flush and fsync the file and, where required and supported, its containing directory. Specify concurrent-writer policy; replacement alone prevents neither lost updates nor cross-file inconsistency.

Protect user-edited data with a recovery/backup policy and bounded retention when overwriting. Version persistent formats and test old data. Checkpoint only committed progress; crash recovery must distinguish complete, partial, and uncertain work. Record redacted effective configuration and provenance for reproducible jobs.

## Subprocesses

Use argument arrays, no untrusted shell interpolation, controlled environment and working directory, bounded output, and checked exit status. Resolve executables deliberately. Timeout/cancellation must terminate and reap children; handle descendants when the command can spawn them. Drain stdout/stderr without deadlock and treat output as untrusted data.

## Checklist

- [ ] Calls, bodies, retries, queries, and process output are bounded.
- [ ] Repeatability, uncertain completion, transaction scope, and concurrency policy are explicit.
- [ ] For each remote create: if it times out after succeeding, what finds the resource, including after a restart?
- [ ] Persistence meets atomicity, durability, compatibility, and recovery requirements.
- [ ] Tests cover partial failure and real-system guarantees, not only successful mocks.
