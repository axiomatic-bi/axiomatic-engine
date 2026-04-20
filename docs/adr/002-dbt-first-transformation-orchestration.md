# ADR 002: dbt-First Transformation Orchestration

## Status

Accepted

## Context

The engine already provides a contract-first ingestion path (`dlt`) into warehouse destinations, but transformation execution was missing. External project runners were expected to stay thin, while transformation logic needed to remain engine-agnostic and compatible with CI environments.

We considered three approaches:

- engine-native SQL planning and execution
- dbt-first transformation execution
- hybrid with immediate file-based execution and later dbt integration

We selected a dbt-first path because dependency graphing, model ordering, and test execution are mature capabilities in dbt and should not be reimplemented in the engine at this stage.

## Decision

Adopt a dbt-first transformation stage orchestrated by the engine:

- keep one pipeline entrypoint in Python (`Pipeline.run(...)`)
- ingest with `dlt` first, then run transformations via a transformation adapter
- model dependencies are delegated to dbt (`ref()`/`source()`)
- transformation execution is implemented through contracts and adapters, not directly in `Pipeline`

## Architectural Boundaries

### Contracts

Add `contracts/transformation.py` with strict typing:

- `TransformationKind`
- `TransformationRequest`
- `TransformationResult`
- `TransformationProtocol`

This establishes a stable engine boundary so orchestration code does not depend on dbt-specific details.

### Core

- `core/pipeline.py` remains orchestration-focused (when to run stages)
- `core/ingestion.py` remains responsible for ingestion
- `core/transformation.py` introduces a `Transformer` stage coordinator

### Adapters and Factory Isolation

- dbt execution lives in `adapters/transformation/dbt_adapter.py`
- adapter creation stays centralised in `adapters/factory.py`
- `Pipeline` requests a transformation adapter via the factory

This preserves dependency direction and existing factory isolation conventions.

## API Stability Policy

Do not depend on internal `dlt.common.*` APIs for dbt execution. Use documented interfaces or dbt CLI invocation to reduce compatibility risk across upstream version changes.

## Secret Management Strategy

- keep non-sensitive runtime configuration in `AXIOMATIC_*` environment variables
- source sensitive values from local non-committed env files and CI secret stores
- use dbt `profiles.yml` with `env_var(...)` placeholders for secrets
- avoid committing credentials or embedding tokens in static repository files

## Warehouse Compatibility Policy

Warehouse kind determines dbt compatibility checks. Initial implementation scope is MotherDuck-first:

- `motherduck` is enabled for dbt transformations
- other warehouse kinds currently raise explicit `NotImplementedError`

Future warehouse support (for example BigQuery) requires:

- warehouse adapter support in engine
- matching dbt adapter package support
- explicit factory mapping and validation updates

## Consequences

### Positive

- thinner external project runners
- reuse of mature dbt dependency/test capabilities
- strict, typed transformation contracts
- clear separation of concerns across core orchestration and adapters
- straightforward CI automation with one pipeline command

### Trade-offs

- dbt project scaffolding becomes a required part of transform-enabled projects
- additional adapter and settings surface area in engine
- initial warehouse support is intentionally narrow (MotherDuck-first)
