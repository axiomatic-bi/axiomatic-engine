# Decision 001: Defer ODS Integration to v1.1

**Date**: 2026-05-20
**Status**: Accepted
**Deciders**: User, AI Assistant

## Context
The NHS inequality analysis project requires NHS organisation reference data (ODS) to provide context for RTT commissioner-level data. Initial planning considered using the ODS ORD API for lookups.

## Decision
**Defer ODS integration to v1.1. Use RTT commissioner data directly for v1 analysis.**

## Rationale

1. **ODS API vs Bulk Data**: The ODS ecosystem provides APIs (ORD, FHIR) suited for lookups and reduced datasets, but the ODS Data Search and Export (DSE) service and bulk exports are more stable for analytics pipelines.

2. **DSE API Requires Research**: The DSE API endpoint for automated bulk downloads needs further investigation. The ODS landscape is transitioning from legacy CSV downloads to DSE predefined reports.

3. **RTT Data Already Provides ICB Grains**: NHS England's RTT commissioner files are already aggregated at sub-ICB, ICB, region, and England levels. v1 analysis can proceed using these grains directly without additional ODS joins.

4. **Simpler v1 Scope**: Deferring ODS allows faster delivery of the core ZIP-streaming engine feature and demonstrates RTT analysis capability sooner.

## Consequences

**Positive:**
- Faster v1 delivery
- Focus on generic engine capability (ZIP streaming)
- Simpler dbt models (no ODS joins required)

**Negative:**
- Less rich organisation context in v1 (no trust names, hierarchy details)
- v1.1 will require additional ingestion work

## Related
- [NHS Inequality v1 Plan](../current/nhs-inequality-v1.md)
- GitHub Issue (future): Research DSE API for bulk ODS downloads
