# ADR 004: Axiomatic Extraction Metadata Injection

## Status

Accepted

## Context

Downstream models and audits require a consistent extraction lineage field across resources, regardless of source type.

Relying on source payload fields is not reliable because many upstream APIs and files do not provide uniform extraction timestamps.

## Decision

Inject `_axiomatic_extracted_at_utc` in the base resource wrapper (`BaseResource`) for every emitted record.

- timestamp is generated once per resource iteration cycle
- metadata injection occurs before dlt extraction/normalisation
- lineage field is available to silver/gold models consistently

## Consequences

### Positive

- consistent lineage across source technologies
- simpler downstream modelling and auditing
- no project-specific duplication of extraction timestamp logic

### Trade-offs

- nested child tables may require lineage inheritance from parent joins
- extraction-time semantics differ from event-time semantics and must be documented
