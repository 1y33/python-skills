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

Know what the code reads, writes, owns, and how it fails. Distinguish missing, empty, zero, and None when the value is persisted, crosses an API, or callers branch on it. For risky work, identify failure windows and recovery first.

## Usage, flow, extension

- Design the caller-facing operation first: inputs, result, normal call, actionable errors. Safe defaults for common use; advanced use replaces policy without copying internals. Defaults never hide resource ownership or configuration.
- Keep orchestration readable in execution order and dependency assembly discoverable.
- Reversibility sets design effort: public APIs, persisted formats, schemas, and extension contracts get deliberate design and versioning; easily changed internals stay the simplest thing that works.

### Interfaces first

- Every role that can have more than one implementation is an ABC: I/O boundaries (storage, HTTP, providers, models, cache, notifier), pipeline steps (rules, stages, validators, metrics, callbacks), format variants (loaders, exporters), policies (pricing, scoring, permissions, retry), and handlers picked by key (message types, commands, webhooks).
- Compose explicitly: inject by constructor, run steps from an ordered list (`for rule in rules: rule.apply(ctx)`), pick handlers from a dict. A new variant is one new class plus one line in that list or dict.
- Design for extension: shape each interface for the variants you can foresee (the next backend, format, rule, provider), so adding one later is a new class with no edits to existing code. Implement the variants the task uses now; foreseen variants live in the interface design.
- Not interfaces: plain data (Pydantic models, dataclasses) and a single algorithm with nothing to swap. A test fake alone does not justify an interface.
- If a variant does not fit, first refactor to create the seam without changing behavior, then add the variant as a separate step. Snippets: [patterns](references/patterns.md).

### Contracts

Extension contracts use abc.ABC with @abstractmethod, not typing.Protocol; use Protocol only to accept types you do not own. Keep abstract methods few and inherited defaults contract-preserving. Prefer deep modules: a small interface over substantial behavior. The ABC docstring states only what the signature cannot: ordering, mutation, failure. Composition stays visible: no import-time discovery across packages or event buses; a decorator registry in the contract's own module is fine.

## Structure and readability

Keep cohesive logic together in a few readable functions; I/O enters through injected interfaces, so logic tests need no mocks. Extract a function for reuse or to isolate an effect; never one-use forwarding helpers, one-line aliases, or a helper that only replaces a useful comment. Use classes for owned state, lifecycle, or cohesive behavior. Do not split by line count or force one module, one class per file, role folders, factories, or service/repository layers; do split a function that runs several stages and a class whose methods share no state. Orchestration reads as a short list of named stage calls with typed results.

Module boundaries follow responsibility and dependency direction; isolate transport and storage details that would couple reusable logic. Keep related definitions nearby, exports discoverable, imports acyclic and free of side effects.

Name abstractions by domain responsibility and concrete classes by the behavior or backend that distinguishes them; if two classes cannot be told apart that way, reconsider the split. Avoid generic names, suffix-only distinctions, and deep inheritance.

Names say what the thing is in the domain, locals and parameters included. No single-letter or abbreviated names outside short math expressions and loop indices; no alias that renames an existing call (`def _m(fn, *a): return ops.Map(fn, a)`), call the real thing. Use a leading underscore only to hide a name from a module's public API; internal modules do not underscore everything. A helper copied into two modules becomes one named function in a shared module. Use domain names consistently, explicit signatures, keyword-only confusable arguments, and ordinary control flow.

Comments and docstrings carry only what names, types, and code cannot: reasons, hidden constraints, non-obvious contracts, usually in one sentence. Clear functions and self-explanatory classes, public ones included, need none. Delete narration and boilerplate.

## Types, validation, values

- Annotate changed functions and public contracts; let locals infer. Use the configured checker; new maintained libraries and services pass `mypy --strict` or equivalent; scripts and training code annotate public functions; changed files add no new errors. Keep Any and suppressions narrow; never cast away a violated contract.
- Match the supported Python version; use built-in generics and `X | Y`. Pick Callable, dataclass, enum, or union by actual shape, ABCs for class interfaces. Closed value sets are enums (StrEnum when serialized), compared by member, never raw strings. Records are frozen dataclasses, not `dict[str, Any]` or tuples; serialize at the I/O edge.
- Parse, don't validate: convert untrusted input into a precise type once at entry so inner code never re-checks it. Annotations are not runtime validation. Use simple checks for simple inputs and Pydantic for structured schemas, specifying coercion, unknown fields, size limits, and cross-field rules. Never use assert for external validation; validators never do I/O.
- Model incompatible states explicitly; exhaust closed unions with assert_never. Prefer immutable shared values (frozen is shallow). No mutable defaults or undocumented aliasing.
- Preserve meaningful order: dicts keep insertion order; sets and directory listings do not. Sort only when canonical order is required. Check equal lengths before zipping when truncation loses data.
- Aware datetimes for instants, explicit rules for civil time, monotonic clocks for durations, units in names. Decimal with stated rounding for exact decimals; define tolerance, non-finite, zero-division, and overflow behavior where numerics matter.
- Do not add `from __future__ import annotations` (lint-banned; removal caveats in [project-setup](references/project-setup.md)). Quote one forward reference or use typing.Self.

## Errors, resources, state

Use specific built-in exceptions; add custom types only when callers handle them differently. Return typed outcomes for expected branches, never ambiguous empty values. Preserve safe causes; redact secrets and upstream details, including in chained tracebacks.

Catch only where recovery or reporting happens; broad catches only at explicit containment boundaries, and even there programmer errors (KeyError, TypeError, AttributeError, AssertionError) propagate: catch the named failure the callee raises. Never swallow cancellation or exit signals. Tolerated failure needs an observable, documented policy; report each exception once at the responsible boundary.

Resources have explicit owners and context-managed cleanup, including partial acquisition. Close what you own, not what you borrow. Bound waits with a deadline and bound retries, buffers, queues, and caches with overflow behavior. Cache keys include every input that changes the result. Assemble configuration and dependencies explicitly; no service locators. Test supplied dependencies with `is None`, not truthiness.

Configure logging only at entrypoints ([observability](references/observability.md)); use lazy arguments and keep secrets out of logs and diagnostics. Use pathlib, explicit encodings, safe parsers, and importlib.resources for package data. Persistence meets its required atomicity and durability. CLIs write data to stdout and diagnostics to stderr, exit non-zero on failure, and show expected user errors without tracebacks.

## Verification and delivery

- Test observable contracts by risk: normal path, boundaries, failure, cleanup, each fixed regression. No per-helper test quota.
- Prefer real components and small fakes at real seams. Unit tests control clocks, network, randomness, and order; integration tests cover what fakes cannot. When a fake stands in for a third-party API, pin its shape with recorded real responses.
- Measure representative time and peak memory before optimizing; keep correctness checks beside benchmarks.
- Check exports, entrypoints, configuration, and compatibility end to end. New extension points get a substitution test through the public path; changed formats get compatibility tests.
- Run the repository's formatter, lint, type checks, and relevant tests. If a public symbol, schema, or module imported by several packages changes, run the full suite and type-check the whole package. Report failures and unrun checks; a build does not prove behavior. Never delete or loosen an assertion, add a skip, or widen a suppression to pass; fix the code or report.
- Before using a function, argument, or package not already used in the repository, confirm it exists in the installed version (its source, `help()`, or docs, not memory) and that a new package name is the real project.
- Before reporting, read the whole diff as a reviewer: what else writes this state, what if it runs twice, concurrently, or after a crash, what a failure costs, and what can be deleted.
- Report briefly: what changed, how to call it, where the next variant goes, checks run and not run.
