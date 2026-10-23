# Extensible processing

Read when designing multi-stage execution, interchangeable transformations, or resumable processing. Separate stable execution from variable work without prescribing classes, subpackages, or an event bus.

## Composition and discoverability

Make execution order and assembly explicit. Supply a useful default composition and a supported way to replace or extend it without copying the execution loop. Prefer an ordered sequence when order suffices; use dependency graphs only when partial ordering or scheduling requires them. Reject unknown dependencies, duplicates where invalid, and cycles before execution.

Keep implementations near their contracts. A new component should normally require its implementation and explicit composition change, not edits across a central type switch and unrelated modules. Do not use cross-package import-time registration or plugin discovery merely to avoid an explicit list; a decorator registry in the contract's module is fine (see patterns). Document actual paths, symbols, and the extension procedure.

## Transformation contracts

Define input/output representations, preconditions, postconditions, preserved invariants, mutation/aliasing, determinism, and failure behavior. Choose functions for stateless transformations and objects for owned state or lifecycle. Avoid separate abstract roles that have identical obligations. Pass only needed configuration; do not invent config classes for components with no configuration.

Track dependencies between stages. Values derived from a stage's output are invalidated or recomputed when that output changes. Cache keys include all semantic inputs and relevant versions; object identity alone is not proof of unchanged contents. Do not expose mutable cache entries to consumers.

For iterative execution, define convergence, progress, termination bounds, and non-convergence behavior. Reordering, skipping, or parallelizing stages requires preservation of dependencies and observable semantics. Validate invariants at useful boundaries; retain provenance for diagnosing where an invalid result originated.

## Effects, outputs, and recovery

Keep computation and effects distinguishable; use explicit return values rather than hidden cross-stage state. Stateful stages declare reset/reuse and concurrency rules. Outputs may be direct calls or callbacks; events/sinks are appropriate only when independent subscription or delivery policy is needed.

Define per-item and per-run failure policy: stop, retry, skip with reporting, or partial result. Bound queues, tasks, buffers, and output accumulation; stream when inputs can exceed memory. Preserve meaningful order and seed randomness when reproducibility matters.

Resumable execution needs versioned checkpoints, committed-progress semantics, and compatible input/configuration fingerprints. Handle a crash between an external effect and its checkpoint through idempotency or reconciliation. Do not claim replay safety merely because a progress file exists. Read external-I/O and concurrency references when implementing those mechanisms.

## Verification

When the pipeline exposes an extension point, test an alternate implementation through the public runner. Test ordering/dependency rejection and relevant invariants. Use differential tests for semantics-preserving transformations, property tests for algebraic guarantees, and golden files only where output representation is contractual. Measure stage and end-to-end cost on representative inputs; faster invalid output is a regression.

## Checklist

- [ ] Default usage, composition, and the next credible extension are discoverable.
- [ ] Contracts cover invariants, ordering, mutation, analysis invalidation, and lifecycle.
- [ ] Iteration, memory, failure, and recovery policies have explicit limits.
- [ ] Public-path substitution and relevant semantic-preservation checks pass.
