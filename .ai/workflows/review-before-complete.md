---
description: Review process and medallion architecture conventions
---

# Mandatory Review Process

Before marking any task as complete and committing changes, the following steps MUST be followed:

## 1. Complete Implementation
- Finish the code changes for the task
- Do NOT mark todo as complete yet

## 2. Independent Review (REQUIRED)
- Spawn an independent `code_search` agent to review the changes
- The agent must check:
  - Architecture compliance (medallion layers, separation of concerns)
  - SQL correctness and efficiency
  - Naming conventions
  - Data modeling best practices
  - Logic errors or edge cases
- Wait for review feedback

## 3. Address Feedback
- Review the agent's findings
- Fix any issues identified
- If significant changes made, re-run review
- Repeat until no more feedback

## 4. User Confirmation
- Present summary of changes and review findings to user
- Ask: "Are you happy with these changes?"
- Wait for explicit user approval

## 5. Commit (Only After User Approval)
- Commit the changes
- Then mark todo as complete
- Then move to next task

## NEVER:
- Mark todos complete before review
- Skip the independent review step
- Commit without user approval
- Rush to the next task without confirmation

---

# Medallion Architecture Conventions

## Bronze Layer
- **Source**: dlt-ingested raw data (no dbt models)
- **Purpose**: Raw data ingestion with minimal transformation
- **Reference**: Use `{{ source('schema_name', 'table_name') }}` in dbt

## Silver Layer
- **Purpose**: Cleaned, typed, and lightly transformed data
- **Naming conventions**:
  - `stg_*.sql` - Staging models that cast, rename, and clean from bronze
  - `int_*.sql` - Intermediate models with business logic and aggregations
- **Examples**:
  - `stg_rtt_commissioner.sql` - Casts columns, renames from source
  - `int_rtt_metrics_by_commissioner.sql` - Calculates breach metrics

## Gold Layer
- **Purpose**: Business-ready analytical models
- **Naming conventions**:
  - `fct_*.sql` - Fact tables (metrics, events)
  - `dim_*.sql` - Dimension tables (descriptive attributes)
- **Examples**:
  - `fct_waiting_times_by_icb.sql` - ICB-level metrics with benchmarks

## Reference Chain
```
{{ source('bronze', 'table') }}  -- Bronze (dlt-ingested)
    ↓
{{ ref('stg_table') }}           -- Silver staging
    ↓
{{ ref('int_metrics') }}         -- Silver intermediate
    ↓
{{ ref('fct_analytics') }}       -- Gold business model
```

## Example: fake_store Pattern
```
models/
├── sources.yml                  # Points to dlt bronze tables
├── silver/
│   ├── stg_products.sql         # Cast/rename from source
│   ├── stg_carts.sql            # Cast/rename from source
│   ├── int_cart_summary.sql     # Business logic
│   └── ...
└── gold/
    ├── fct_cart_items.sql      # Business-ready facts
    └── dim_products.sql        # Business-ready dimensions
```
