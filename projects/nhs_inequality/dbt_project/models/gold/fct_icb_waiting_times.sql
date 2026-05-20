{{
  config(
    materialized='table',
    schema=env_var('AXIOMATIC_SCHEMA_GOLD', 'gold')
  )
}}

--
-- Star Schema Fact Table: ICB Waiting Times
-- Grain: ICB × Period × RTT Part Type
--
-- Degenerate dimension keys: period, icb_code, rtt_part_type (SK=BK pattern)
-- Denormalized attributes for query convenience
-- Long-wait tail focus: 52+, 65+, 78+, 104+ week metrics emphasized
--

with icb_metrics as (
    -- ICB-level metrics from silver
    select
        period,
        commissioner_org_code as icb_code,
        rtt_part_type,
        commissioner_org_name as icb_name,
        commissioner_parent_org_code as region_code,
        commissioner_parent_name as region_name,

        total_waiting_list,
        total_waiting_list - count_over_18_weeks as count_within_18_weeks,
        count_over_18_weeks,
        count_over_52_weeks,
        count_over_65_weeks,
        count_over_78_weeks,
        count_over_104_weeks,

        pct_within_18_weeks,
        pct_over_52_weeks

    from {{ ref('int_rtt_metrics_by_commissioner') }}

    where commissioner_org_code is not null
      and commissioner_org_code != ''

      -- ICB-level: 3-character codes
      and length(trim(commissioner_org_code)) = 3

      -- Exclude England-level rows
      and not (upper(commissioner_org_code) like 'X%')
      and not (upper(commissioner_parent_org_code) like 'X%')

      -- Exclude regional rows
      and not (commissioner_org_code like 'Y%')
      and not (commissioner_parent_org_code like 'Y%')
),

england_benchmark as (
    -- Official England totals for variance calculation
    select
        period,
        england_pct_within_18_weeks,
        england_pct_over_52_weeks
    from {{ ref('int_icb_benchmarks') }}
    where level_type = 'England'
)

select
    -- ========================================
    -- DEGENERATE DIMENSION KEYS (SK=BK pattern)
    -- ========================================
    i.period,
    i.icb_code,
    i.rtt_part_type,

    -- ========================================
    -- DENORMALIZED DIMENSION ATTRIBUTES
    -- ========================================
    i.icb_name,
    i.region_code,
    i.region_name,

    -- ========================================
    -- MEASURES: Waiting list counts
    -- ========================================
    i.total_waiting_list,
    i.count_within_18_weeks,
    i.count_over_18_weeks,
    i.count_over_52_weeks,
    i.count_over_65_weeks,
    i.count_over_78_weeks,
    i.count_over_104_weeks,

    -- ========================================
    -- MEASURES: Percentages (using canonical totals)
    -- ========================================
    round(i.pct_within_18_weeks, 2) as pct_within_18_weeks,

    round(
        100.0 * i.count_over_18_weeks / nullif(i.total_waiting_list, 0),
        2
    ) as pct_over_18_weeks,

    round(
        100.0 * i.count_over_52_weeks / nullif(i.total_waiting_list, 0),
        2
    ) as pct_over_52_weeks,

    round(
        100.0 * i.count_over_65_weeks / nullif(i.total_waiting_list, 0),
        2
    ) as pct_over_65_weeks,

    round(
        100.0 * i.count_over_78_weeks / nullif(i.total_waiting_list, 0),
        2
    ) as pct_over_78_weeks,

    round(
        100.0 * i.count_over_104_weeks / nullif(i.total_waiting_list, 0),
        2
    ) as pct_over_104_weeks,

    -- ========================================
    -- MEASURES: Long-wait tail index (custom inequity metric)
    -- ========================================
    -- Emphasizes tail concentration: (pct_over_52)^2
    -- ICBs with same 52+ % but different distributions will differ on tail index
    round(
        power(
            100.0 * i.count_over_52_weeks / nullif(i.total_waiting_list, 0),
            2
        ) / 100.0,
        4
    ) as long_wait_tail_index,

    -- ========================================
    -- MEASURES: Variance from England benchmark
    -- ========================================
    round(
        i.pct_within_18_weeks - e.england_pct_within_18_weeks,
        2
    ) as variance_from_england_18wk,

    round(
        (100.0 * i.count_over_52_weeks / nullif(i.total_waiting_list, 0))
        - e.england_pct_over_52_weeks,
        2
    ) as variance_from_england_52wk,

    -- ========================================
    -- MEASURES: Performance vs England
    -- ========================================
    case
        when i.pct_within_18_weeks >= e.england_pct_within_18_weeks
        then 'At or above England average'
        when i.pct_within_18_weeks >= e.england_pct_within_18_weeks - 5
        then 'Within 5% of England average'
        else 'More than 5% below England average'
    end as performance_vs_england,

    -- ========================================
    -- MEASURES: 18-week target compliance
    -- ========================================
    case
        when i.pct_within_18_weeks >= 95 then 'Compliant (>=95%)'
        when i.pct_within_18_weeks >= 90 then 'Near target (90-95%)'
        when i.pct_within_18_weeks >= 80 then 'Below target (80-90%)'
        else 'Well below target (<80%)'
    end as target_compliance_category,

    -- ========================================
    -- METADATA
    -- ========================================
    current_timestamp as model_run_at

from icb_metrics i
left join england_benchmark e
    on i.period = e.period

order by i.period, i.icb_code, i.rtt_part_type
