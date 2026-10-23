# Project setup

Read when changing environments, packaging, dependencies, tooling, or CI. Preserve existing tools; use uv for new projects. Choose a supported Python version compatible with deployment and dependencies; declare requires-python and align checker/linter targets. Use newer syntax only within that range.

## Environment and dependencies

- Run project tools through the managed environment; do not install into system Python. With uv, use uv run and commit the project lockfile. CI uses uv sync --locked so stale locks fail rather than silently resolve.
- Declare direct runtime dependencies separately from development tools and optional features. Add only what the work uses; no default HTTP, settings, async, or property-testing bundle.
- Prefer existing code, stdlib, then installed dependencies. Check maintenance, licensing, security, platform wheels, and interpreter support before adding a package. Upgrade deliberately and test the affected contracts.
- Applications lock deployment resolution. Published libraries declare tested compatibility ranges rather than forcing consumers onto the development lockfile. Test minimum supported dependencies as well as current resolutions when publishing compatibility claims.
- Standalone scripts can use PEP 723 metadata and uv run; lock them when reproducibility matters. Importability alone does not require an installed package or application layers.

## Packaging and usability

Choose layout for installation and ownership, not a template. Use src layout for distributable packages when it prevents accidental working-tree imports; a local script needs no package scaffold. Expose stable entrypoints and exports. Remove or rename a public symbol only after a release that warns (`warnings.deprecated` on 3.13+, else DeprecationWarning) naming the replacement and removal version. Keep library imports independent of CLI startup and optional backends.

Load configuration once at startup into a typed settings object (pydantic-settings where available) and refuse to start when a required value is missing or invalid. Namespace environment variables with an application prefix. Pass settings or their values to components; do not read os.environ deep in the code.

Validate a built wheel in a clean environment outside the source checkout. Check package data, entrypoints, py.typed for typed distributions, and optional-dependency errors. Use importlib.resources for bundled assets. A working editable install does not prove a release artifact works.

## Checks and upgrades

Use one formatter. Default new maintained projects to Ruff, mypy, and pytest; preserve equivalent existing tools. Start with useful lint rules, not every rule family. Prefer a lint rule over a written convention: it checks every change at no cost. Default for new projects, and a target when tightening existing ones (review findings, do not blanket-autofix):

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "TID251", "BLE", "S110", "FBT", "ERA", "ASYNC", "C901"]

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"__future__.annotations".msg = "breaks runtime annotation consumers"

[tool.ruff.lint.mccabe]
max-complexity = 15
```

Fix C901 by simplifying branches (see the python-dev patterns reference), not by extracting one-use helpers.

The import stringifies annotations, breaking runtime consumers (Pydantic, FastAPI, dataclasses, singledispatch) for names imported under TYPE_CHECKING or defined locally; 3.14+ evaluates lazily anyway. Remove it only as its own step or when the task changes that file's annotations: on 3.13 and older, removal evaluates annotations at import, so TYPE_CHECKING-only names must become runtime imports or be quoted. Introspect annotations through documented APIs (annotationlib on 3.14+). Keep `lint.future-annotations` off; when enabled, some fixes insert the banned import. Avoid lint-driven function fragmentation. Scope stricter typing to changed/new packages without hiding errors elsewhere.

Tests use strict marker registration and visible deprecations. Introduce warnings-as-errors when dependencies support it; suppress known warnings narrowly. Register integration and hardware tests explicitly. Local and CI commands use the same locked tools. Run supported interpreter versions where compatibility is promised; audit the deployed dependency set for vulnerabilities.

Evaluate runtime upgrades through tests and benchmarks, not novelty. On 3.14+, annotation introspection and multiprocessing behavior deserve migration checks. Free-threaded builds require separate dependency compatibility and race testing; they are not an automatic performance upgrade. Development mode and resource warnings help expose lifecycle bugs.

## Checklist

- [ ] Version targets, dependencies, lock policy, and commands agree with deployment.
- [ ] Installation and public entrypoints work without accidental checkout imports.
- [ ] Tools are scoped, dependencies used, and CI reproduces local checks.
- [ ] Relevant interpreter, dependency, and artifact compatibility is tested.
