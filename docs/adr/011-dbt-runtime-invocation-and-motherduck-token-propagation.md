# ADR 011: dbt Runtime Invocation And MotherDuck Token Propagation

## Status

Accepted

## Context

Transformation execution is run by `DbtTransformationAdapter` through subprocess invocation.

Two operational issues emerged:

- `dbt` executable was not always available on PATH in local and CI contexts
- MotherDuck authentication for dbt could trigger interactive fallback when only `AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN` was present and `MOTHERDUCK_TOKEN` was missing

These failures were environmental and reduced pipeline reliability despite valid project configuration.

## Decision

Harden dbt runtime invocation in the adapter:

- prefer `dbt` on PATH when available
- fallback to Python module execution when `dbt` binary is unavailable:
  - `python -m dbt.cli.main`
- resolve absolute project and profiles directories before subprocess execution
- propagate `AXIOMATIC_MOTHERDUCK_ACCESS_TOKEN` to `MOTHERDUCK_TOKEN` when the latter is unset

## Consequences

### Positive

- improved portability across developer machines and CI agents
- fewer environment-specific failures for dbt command discovery
- reduced likelihood of interactive MotherDuck auth prompts during automated runs
- clearer runtime behaviour for transform stage execution

### Trade-offs

- adapter includes additional runtime branching and environment handling
- fallback path depends on dbt module importability in the selected Python environment
- token propagation requires explicit documentation to avoid ambiguity

## Security Notes

- token values remain sourced from environment variables
- adapter does not persist or log token contents
- precedence remains explicit token variable (`MOTHERDUCK_TOKEN`) when already set
