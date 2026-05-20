# NHS Inequality Analysis Project Plan - v1

Build a portfolio project analysing how NHS waiting times (RTT) patterns vary across commissioners/ICBs and deprivation context over the last 12 months, demonstrating the Axiomatic Engine's capabilities for public health data engineering.

## Data Sources

### 1. RTT (Referral to Treatment) Waiting Times
- **Source**: NHS England Statistics (CSV in ZIP via HTTP)
- **URL Pattern**: `https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/{year}/{month}/Full-CSV-data-file-{Mon}{YY}-ZIP-{size}-revised.zip`
- **Data**: Monthly snapshots, 12 months historical
- **Structure**: Provider-level and Commissioner-level files
- **Key Fields**: Organisation code, treatment function code, waiting time bands, patient counts
- **Access**: Public HTTP download, no authentication

### 2. ODS (Organisation Data Service) - v1.1
- **Status**: Deferred to v1.1 (DSE API requires further research)
- **Source**: NHS ODS Data Search and Export (DSE) API or predefined reports
- **Data**: NHS organisation reference data (trusts, ICBs, sub-ICBs)
- **Note**: v1 uses RTT commissioner data directly (already aggregated at ICB/sub-ICB/region/England levels)

### 3. IMD (Index of Multiple Deprivation) 2019 - v1.1
- **Source**: ONS Open Geography Portal
- **URL**: `https://open-geography-portalx-ons.hub.arcgis.com/api/download/v1/items/ad50773cd40e4907a450c5d8954a9d26/csv?layers=0`
- **Data**: LSOA-level deprivation scores for England
- **Key Fields**: LSOA code, IMD rank, IMD decile, domain scores
- **Access**: Public HTTP CSV download

## Engine Upgrades Required

### 1. HTTP Source Enhancement: Archive Support (Generic)
**File**: `src/axiomatic_engine/sources/file/http_stream.py`

Add generic support for extracting delimited files from HTTP-delivered archives. Design must be source-agnostic and reusable for any archive-delimited file combination (e.g., government open data, research datasets, vendor extracts):

- Add `archive_format: Literal["zip"] | None` parameter to `HttpFileResourceDefinition` (extensible for "tar", "7z" in future)
- Add `archive_member: str | None` parameter (path to specific file within archive, e.g., "data/file.csv")
- Implement `_get_archive_stream()` method using `zipfile.ZipFile` with `io.BytesIO` for memory-efficient streaming
- Auto-detect `.zip` extension via `_infer_archive_format()` (consistent with existing `_infer_compression()` pattern)
- Support nested member paths (e.g., "subdir/data.csv")
- Archive extraction feeds into existing `_get_stream()` decompression pipeline (enables `.csv.gz` inside `.zip`)

**Configuration Example** (any project, not NHS-specific):
```python
HttpFileResourceDefinition(
    name="monthly_data",
    url="https://example.org/data/release_2025.zip",
    archive_format="zip",  # Auto-detected if URL ends with .zip
    archive_member="release_2025/csv/monthly_metrics.csv",
    delimiter=",",
)
```

## Project Structure

```
projects/nhs_inequality/
├── README.md                      # Project documentation
├── .env.example                   # Environment variable template
├── run_pipeline.py               # Entrypoint (similar to fake_store)
├── dbt_project/
│   ├── dbt_project.yml           # dbt configuration
│   ├── models/
│   │   ├── bronze/               # Raw ingested data
│   │   │   ├── stg_rtt_commissioner.sql     # Commissioner-level RTT (ICB grain)
│   │   │   ├── stg_ods_organisations.sql     # Bulk ODS reference data
│   │   │   └── stg_imd_lsoa.sql            # IMD reference (used where analytically sound)
│   │   ├── silver/               # Cleaned and joined
│   │   │   ├── int_rtt_with_icb_context.sql
│   │   │   └── int_icb_deprivation_context.sql
│   │   └── gold/                 # Analysis-ready
│   │       └── fct_waiting_times_by_icb_and_deprivation.sql
│   └── analyses/
│       └── waiting_time_patterns_by_icb.sql
└── data/                         # Local reference data (if needed)
```

## Analysis Approach

### Research Question
"How do RTT waiting-time patterns vary across commissioners/ICBs and deprivation context over the last 12 months?"

### Analytical Framing
- **Use commissioner-level RTT data** - already aggregated to sub-ICB, ICB, region, and England grains by NHS England
- **Avoid postcode-to-deprivation pitfalls** - provider-postcode-to-IMD only gives deprivation at the provider location, not the waiting-list population
- **Defensible claims**: "Commissioners/ICBs serving or located in more deprived areas show different waiting-time patterns" rather than "more deprived patients wait longer"

### Geographic Scope
- **Primary Focus**: One focal ICB or sub-ICB (e.g., Cheshire and Merseyside ICB or NHS Cheshire East sub-ICB)
- **Benchmarks**: Regional (North West) and England-level aggregates for comparison
- **Rationale**: RTT commissioner files already provide clean ICB/sub-ICB aggregation; avoids hand-picked geography assumptions

### Key Metrics
1. **Waiting time patterns** by ICB/sub-ICB with deprivation context
2. **18-week target compliance** variation across commissioners
3. **ICB vs regional vs England benchmarks**
4. **Time trend analysis** (12 months)

### Join Logic
1. RTT commissioner data (by ODS code) -> ODS reference data (ICB/sub-ICB hierarchy)
2. Where analytically sound: ICB/sub-ICB -> deprivation context (via area-based IMD, not patient-level)
3. Aggregate waiting time metrics by ICB with England/region benchmarks

## Implementation Phases

### Phase 1: Engine Upgrade - ZIP Support
1. Extend `HttpFileResourceDefinition` with archive parameters
2. Implement ZIP streaming in `HttpStreamResource`
3. Add tests for ZIP handling
4. Run quality gate

### Phase 2: RTT Ingestion (Single Month)
1. Create `nhs_inequality` project structure
2. Configure RTT source using generic archive support:
   ```python
   HttpFileResourceDefinition(
       name="rtt_commissioner_mar25",
       url="https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/07/Full-CSV-data-file-Mar25-ZIP-4M-revised.zip",
       archive_format="zip",  # Generic engine capability
       archive_member="Full CSV data file Mar25 (ZIP 4M) revised/ Commissioner Mar25 revised.csv",
       delimiter=",",
   )
   ```
3. Configure DuckDB warehouse
4. Verify bronze ingestion

### Phase 3: Analysis with RTT Commissioner Data (v1)
1. Build dbt models using commissioner-level RTT data
2. Analyse patterns at ICB/sub-ICB/region/England grains (already provided in RTT data)
3. Create benchmarks: focal ICB vs region vs England
4. Document methodology

### Phase 4: ODS & IMD Integration (v1.1) - Deferred
1. Research DSE API for automated ODS downloads
2. Add ODS reference data for richer organisation context
3. Add IMD as contextual reference (area-level only)
4. Enhanced analysis with organisation hierarchy

### Phase 5: dbt Models
1. Create bronze staging models
2. Build silver intermediate models with joins
3. Create gold fact table for analysis
4. Add simple analyses/queries

### Phase 6: Time Series (12 months)
1. Create multiple RTT resources for historical months
2. Add incremental logic if needed
3. Test multi-month joins

### Phase 7: Documentation
1. Write project README
2. Document methodology
3. Summarise findings

## Success Criteria

- [ ] Engine can ingest CSV-from-ZIP via HTTP
- [ ] Bronze layer contains clean RTT commissioner data
- [ ] Silver layer cleans and prepares RTT commissioner data at ICB/sub-ICB/region/England grains
- [ ] Gold fact table enables waiting time patterns by commissioner level
- [ ] Analysis reveals how waiting-time patterns vary across ICBs with regional/national benchmarks
- [ ] All quality gates pass
- [ ] Project serves as portfolio piece demonstrating public health data engineering

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| NHS URL patterns change | Use recent month first, document URL structure |
| Postcode-to-LSOA mapping complexity | Use ONS postcode lookup dataset |
| Large ZIP files (4MB x 12 months) | Streaming decompression, no local storage |
| ODS integration deferred | Document in v1.1 roadmap; v1 uses RTT grains directly |
| Area-level deprivation vs patient-level claims | Clear documentation of analytical limitations (v1.1) |
