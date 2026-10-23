---
name: python-refactor
description: Behavior-preserving Python cleanup and restructuring. Use for refactoring, modernization, readability, reuse, or reducing extension cost; follows python-dev through scoped audits, characterization tests, and verified incremental changes.
---

# Python refactoring

Load python-dev unless its unchanged core remains in context. Use its reference routing for concerns actually audited or changed. It defines engineering criteria, not a mandatory architecture. Do not refactor code merely because it lacks layers, interfaces, dataclass returns, or prescribed filenames. Migrate existing Protocols to ABCs only within the agreed scope, preserving consumers.

## Baseline

Confirm scope and compatibility requirements. Trace public entrypoints, callers, data flow, dependency direction, and tests. Identify common usage and credible extension points. Record existing failures from configured checks before changes; do not hide them or require a tooling migration to begin.

Pin observable behavior with characterization tests where coverage is missing: outputs, effects, ordering, failure contracts, and cleanup. Use real components unless they need network, credentials, or more than a few seconds of setup, and fakes at controllable boundaries. Preserve unstable values only to the extent the contract requires; do not normalize away meaningful differences. Integration tests establish persistence and concurrency guarantees that fakes cannot.

## Audit

Report actionable findings with path, symbol or line, evidence, consequence, and proposed check. Rank by impact:

- Correctness/security: violated invariants, unvalidated boundaries, data loss, leaked resources, races, unsafe retries, swallowed failures, or exposed secrets.
- Usability/change cost: difficult normal invocation, hidden assembly, scattered policy, cross-module edits for one extension, mutable cross-stage state, or hard-to-follow call chains.
- Maintainability: ambiguous names/types, classes indistinguishable by responsibility or behavior, duplicated stable behavior, `assert isinstance` on the code's own data, `getattr` dispatch on strings, untyped `**fields` bags, if/elif chains over closed sets, dependency cycles, stale comments, or unnecessary adapters and packages.

Size alone is not a finding. Missing abstractions are not defects without a concrete need. Evaluate whether removing, combining, or relocating code would clarify the flow before extracting more helpers. Keep abstractions that protect real contracts even if they have one current implementation.

Present findings before implementation unless the user authorized proceeding. For broad work, agree on scope and compatibility before restructuring.

## Plan and execute

Use small, independently verifiable steps. Each names the affected contracts, files, expected benefit, and checks. Order by dependencies and risk rather than a fixed ladder of types, layers, and factories.

- Separate structural changes from bug fixes, format sweeps, and behavior changes. A newly discovered bug gets a distinct regression test and labeled step. Removing `from __future__ import annotations` changes import-time behavior on 3.13 and older; give it its own step.
- Preserve public imports, signatures, errors, serialized formats, and defaults unless a break is approved. Provide compatibility adapters or migrations where consumers need them; do not preserve every private detail.
- Keep cohesive logic together. Extract at meaningful effect, ownership, or extension boundaries; remove forwarding layers that add no policy or contract.
- Introduce validation without silently changing accepted input or coercion. Strengthening validation may be a behavior change, not a refactor.
- Keep default usage simple while exposing justified variation. Walk through the next credible extension and verify it through the public path; do not implement speculative variants.
- Preserve resource lifetime, transaction scope, cancellation behavior, and execution order while moving code. These are behavior, not implementation trivia.
- Run relevant tests and configured lint/type checks after each step. Investigate changed results; never update characterization expectations merely to accept a regression. Revert only your own failing step, preserving unrelated work.

## Completion

Verify public entrypoints and compatibility, then the relevant python-dev checks. Deliver a compact execution map using actual paths/symbols when structure changed, the normal usage path, and the extension location. Report passed checks, pre-existing failures, unrun checks, deferred findings, and concrete debt with revisit triggers. Do not claim behavior preservation without evidence or future-proofing without limits.
