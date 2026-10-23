---
name: python-dev
description: Required for Python implementation, review, refactoring, tests, and project setup. Prioritizes typed contracts, understandable execution, usable APIs, deliberate extension points, and reliable operation. Load before changing Python code or tooling.
---

# Python engineering

Correctness and safety first; then understandability, usability, extension cost, and measured performance. Minimize indirection, not just lines. Apply rules only where their concern exists.

## References

Read this core once; re-read only after it changes or leaves context, never re-append identical guidance. Load a reference when the task changes or audits its concern, not because a nearby file touches it. Its checklist applies to the work in scope.

| Reference | Load for |
| --- | --- |
| [project-setup](references/project-setup.md) | Environment, packaging, dependencies, tooling, CI, configuration loading |
| [async](references/async.md) | Concurrency, task ownership, cancellation, shutdown |
| [fastapi](references/fastapi.md) | HTTP contracts, request handling, app lifecycle |
| [external-io](references/external-io.md) | Remote I/O, persistence, retries, transactions, subprocesses, background jobs |
| [security](references/security.md) | Trust boundaries, network listeners, authorization, secrets, hostile input |
| [pipelines](references/pipelines.md) | Multi-stage, extensible, or resumable processing |
| [observability](references/observability.md) | Logging, tracing, metrics, production diagnosis |
| [patterns](references/patterns.md) | Applying an extension pattern; deciding where validation, branching, and state transitions belong |

## Understand before changing

Trace entrypoints, callers, data flow, dependencies, and tests. Reuse existing behavior. Preserve tooling, compatible APIs, and conventions unless migration is requested. Fix shared causes, not symptoms. Keep unrelated cleanup out of the diff.

Establish inputs, outputs, invariants, failures, mutation, ownership, ordering, and compatibility. Distinguish missing, empty, zero, and None when the value is persisted, crosses an API, or callers branch on it. For risky work, identify failure windows and recovery first.

## Usage, flow, extension

- Design the caller-facing operation first: inputs, result, normal call, actionable errors. Safe defaults for common use; advanced use replaces policy without copying internals. Defaults never hide resource ownership or configuration.
- Keep orchestration readable in execution order and dependency assembly discoverable.
- Reversibility sets design effort: public APIs, persisted formats, schemas, and extension contracts get deliberate design and versioning; easily changed internals stay the simplest thing that works.

### Extension check (reason before building)

Minimal code means no speculative features, not no seams. Before writing a component others will build on, answer in your reasoning:

1. What is the next credible variant (format, backend, provider, metric, stage, policy), from requirements, domain variation, or existing consumers?
2. Where would it go? Target: one new implementation plus one line of explicit composition, no edits to unrelated modules or duplicated orchestration.
3. Which behavior repeats in 3+ places, or in 2 that must change together (retry, timing, caching, validation, logging, setup)?
4. Which pattern makes the variant cheaper without adding indirection to read?

Add the seam now when the task, issue, or docs name variants; two or more production variants exist (test fakes do not count); or the component is a public API, persisted format, extension contract, or a reusable integration layer over interchangeable external systems. Otherwise write direct code; for components others build on, add a `shortcut:` note naming where the seam would go and its trigger. Scripts and one-off jobs need no note. A seam that saves a later rewrite is the minimal change; general minimal-code rules do not override this check. If an extension does not fit, first refactor to create the seam without changing behavior, then add the variant as a separate step.

Patterns (pick by fit; snippets in [patterns](references/patterns.md)): callable parameter; ABC strategy with explicit composition; decorator registry (dict beside the contract, explicitly imported, never cross-package import-time discovery); typed cross-cutting decorator (`functools.wraps`, `ParamSpec`) for retry, timing, tracing, caching, permissions; context manager; template method; pipeline of stages; adapter at transport or storage boundaries; `singledispatch` or `match`; typed result or outcome enum instead of flags and sentinels.

### Seams and contracts

- Choose the smallest sufficient seam: parameter, callable, concrete collaborator, or explicit interface. Prefer deep modules: a small interface over substantial behavior. New class-based extension contracts that implementers subclass use abc.ABC with @abstractmethod, not typing.Protocol; use Protocol only to accept types you do not own; keep abstract requirements minimal and inherited defaults contract-preserving. A test fake alone does not justify an interface.
- Contracts state inputs, outputs, invariants, ordering, mutation, lifecycle, and failures. No hidden registration, dynamic discovery, or event buses without concrete need; a decorator registry in the contract's own module, explicitly imported, is not hidden.

## Structure and readability

Keep cohesive logic together, with a functional core and an imperative shell: pure logic inside, I/O at the edges, so backends attach at the shell and logic tests need no mocks. Extract functions for reuse, independent reasoning, or effect isolation; avoid chains of one-use forwarding helpers, and never extract a helper just to avoid a useful comment. Use classes for owned state, lifecycle, or cohesive behavior. Do not split by line count or force one module, one class per file, role folders, factories, or service/repository layers.

Module boundaries follow responsibility and dependency direction; isolate transport and storage details that would couple reusable logic. Keep related definitions nearby, exports discoverable, imports acyclic and free of side effects.

Name abstractions by domain responsibility and concrete classes by the behavior or backend that distinguishes them; if two classes cannot be told apart that way, reconsider the split. Avoid generic names, suffix-only distinctions, and deep inheritance. Use domain names consistently, explicit signatures, keyword-only confusable arguments, and ordinary control flow.

Comments and docstrings carry only what names, types, and code cannot: reasons, hidden constraints, non-obvious contracts, usually in one sentence. Clear functions and self-explanatory classes, public ones included, need none. Delete narration and boilerplate.

## Types, validation, values

- Annotate changed functions and public contracts; let locals infer. Use the configured checker; new maintained libraries and services pass `mypy --strict` or equivalent; scripts and training code annotate public functions; changed files add no new errors. Keep Any and suppressions narrow; never cast away a violated contract.
- Match the supported Python version; use built-in generics and `X | Y`. Pick Callable, TypedDict, dataclass, enum, or union by actual shape, ABCs for class interfaces, named records over ambiguous tuples.
- Parse, don't validate: convert untrusted input into a precise type once at entry so inner code never re-checks it. Annotations are not runtime validation. Use simple checks for simple inputs and Pydantic for structured schemas, specifying coercion, unknown fields, size limits, and cross-field rules. Never use assert for external validation; validators never do I/O.
- Model incompatible states explicitly; exhaust closed unions with assert_never. Prefer immutable shared values (frozen is shallow). No mutable defaults or undocumented aliasing.
- Preserve meaningful order: dicts keep insertion order; sets and directory listings do not. Sort only when canonical order is required. Check equal lengths before zipping when truncation loses data.
- Aware datetimes for instants, explicit rules for civil time, monotonic clocks for durations, units in names. Decimal with stated rounding for exact decimals; define tolerance, non-finite, zero-division, and overflow behavior where numerics matter.
- Do not add `from __future__ import annotations` (lint-banned; removal caveats in [project-setup](references/project-setup.md)). Quote one forward reference or use typing.Self.

## Errors, resources, state

Use specific built-in exceptions; add custom types only when callers handle them differently. Return typed outcomes for expected branches, never ambiguous empty values. Preserve safe causes; redact secrets and upstream details, including in chained tracebacks.

Catch only where recovery or reporting happens; broad catches only at explicit containment boundaries. Never swallow cancellation or exit signals. Tolerated failure needs an observable, documented policy; report each exception once at the responsible boundary.

Resources have explicit owners and context-managed cleanup, including partial acquisition. Close what you own, not what you borrow. Bound waits with a deadline and bound retries, buffers, queues, and caches with overflow behavior. Cache keys include every input that changes the result. Assemble configuration and dependencies explicitly; no service locators. Test supplied dependencies with `is None`, not truthiness.

Configure logging only at entrypoints ([observability](references/observability.md)); use lazy arguments and keep secrets out of logs and diagnostics. Use pathlib, explicit encodings, safe parsers, and importlib.resources for package data. Persistence meets its required atomicity and durability. CLIs write data to stdout and diagnostics to stderr, exit non-zero on failure, and show expected user errors without tracebacks.

## Verification and delivery

- Test observable contracts by risk: normal path, boundaries, failure, cleanup, each fixed regression. No per-helper test quota.
- Prefer real components and small fakes at real seams. Unit tests control clocks, network, randomness, and order; integration tests cover what fakes cannot. When a fake stands in for a third-party API, pin its shape with recorded real responses. Use property, differential, or fuzz tests when invariants justify them.
- Measure representative time and peak memory before optimizing; keep correctness checks beside benchmarks.
- Check exports, entrypoints, configuration, and compatibility end to end. New extension points get a substitution test through the public path; changed formats get compatibility tests.
- Run the repository's formatter, lint, type checks, and relevant tests. If a public symbol, schema, or module imported by several packages changes, run the full suite and type-check the whole package. Report failures and unrun checks; a build does not prove behavior. Never delete or loosen an assertion, add a skip, or widen a suppression to pass; fix the code or report.
- Before using a function, argument, or package not already used in the repository, confirm it exists in the installed version (its source, `help()`, or docs, not memory) and that a new package name is the real project.
- Before reporting, read the whole diff as a reviewer: what else writes this state, what if it runs twice, concurrently, or after a crash, what a failure costs, and what can be deleted.
- Deliver the usage path and, if structure changed, a map of actual paths and symbols (entrypoint, major calls, data ownership, extension location; a folder tree is not a map). Keep the report short; name concrete debt with its upgrade trigger, never blanket future-proofing claims.
