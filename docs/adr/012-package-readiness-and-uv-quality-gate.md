# ADR 012: Package Readiness And uv Quality Gate

## Status

Accepted

## Context

The engine is transitioning from project-local execution to package-grade distribution and CI enforcement.

Before this ADR:

- packaging metadata and release checks were partially defined
- there was no single standard quality gate command shared by local development and CI
- non-runtime tooling dependencies were not clearly separated from runtime dependencies
- package boundary expectations for `src` layout were not explicitly validated

The project already uses `uv_build` as its build backend, and contributors are using `uv` for dependency and environment workflows.

## Decision

Adopt a uv-first package readiness standard:

- use `[dependency-groups]` in `pyproject.toml` for non-runtime tooling
  - `dev`: packaging and developer workflow tooling (for example `build`, `twine`, `pre-commit`)
  - `test`: test tooling (`pytest`)
- keep runtime dependencies under `[project.dependencies]`
- define one quality gate entry point at `scripts/quality_gate.py` and run it with:
  - `uv run --group dev --group test python scripts/quality_gate.py`
- require the quality gate to execute:
  - unit tests
  - package build (wheel + sdist)
  - metadata validation (`twine check`)
  - wheel boundary checks (`axiomatic_engine` included; `tests/` and `scripts/` excluded)
- enforce explicit package metadata and layout:
  - `readme = "README.md"`
  - `license = { file = "LICENSE" }`
  - explicit `uv_build` module settings for `src` layout

## Consequences

### Positive

- local and CI quality checks are aligned around one command
- runtime and non-runtime dependencies are clearly separated
- package outputs are validated for both correctness and content boundaries
- contributor onboarding is clearer through a standardised workflow

### Trade-offs

- developers must have `uv` installed to run the quality gate, making `uv` the standardised toolchain for the project
- teams using alternative Python workflow tools will need to adapt to project standards
- quality gate execution time increases compared to running only tests

## Operational Notes

- CI should call the same uv-based quality gate command used locally
- release automation should be layered on top of this gate rather than bypassing it
- any future move to tox/nox should be captured in a follow-up ADR
