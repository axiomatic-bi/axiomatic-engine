{{
  config(
    materialized='table',
    schema=env_var('AXIOMATIC_SCHEMA_GOLD', 'gold')
  )
}}

--
-- Gold fact table: ICB waiting time metrics with national benchmarks
-- Grain: ICB x Period
--
-- Enables comparison of any ICB against England averages
--

with icb_metrics as (
    select *
    from {{ ref('int_icb_waiting_metrics') }}
    where not is_england_level
      and not is_regional_level
),

benchmarks as (
    -- Official England totals and ICB peer averages from single source of truth
    select *
    from {{ ref('int_icb_benchmarks') }}
    where level_type = 'England'
)

select
    i.period,
    i.icb_code,
    i.icb_name,
    i.icb_parent_code,
    i.icb_parent_name,

    -- ICB metrics
    i.total_waiting_list,
    i.total_within_18_weeks,
    i.total_over_18_weeks,
    i.total_over_52_weeks,
    i.total_over_65_weeks,
    i.total_over_78_weeks,
    i.total_over_104_weeks,
    i.pct_within_18_weeks,
    i.pct_over_18_weeks,
    i.pct_over_52_weeks,
    i.pct_over_65_weeks,
    i.pct_over_78_weeks,
    i.pct_over_104_weeks,

    -- Official England benchmarks (from source rows, not derived from ICB peers)
    b.england_pct_within_18_weeks as england_18wk_target_pct,
    b.england_total_over_52_weeks as england_total_long_waiters,
    b.england_total_over_65_weeks as england_total_over_65_weeks,
    b.england_total_over_78_weeks as england_total_over_78_weeks,
    b.england_total_over_104_weeks as england_total_over_104_weeks,

    -- ICB peer statistics (explicitly not official England totals)
    b.icb_avg_pct_within_18_weeks,
    b.icb_best_pct_within_18_weeks,
    b.icb_worst_pct_within_18_weeks,

    -- Variance from official England benchmark
    round(i.pct_within_18_weeks - b.england_pct_within_18_weeks, 2)
        as variance_from_england_target,

    -- Performance vs official England benchmark
    case
        when i.pct_within_18_weeks >= b.england_pct_within_18_weeks
        then 'At or above England average'
        when i.pct_within_18_weeks >= b.england_pct_within_18_weeks - 5
        then 'Within 5% of England average'
        else 'More than 5% below England average'
    end as performance_vs_england,

    -- 18-week target compliance (95% is NHS constitutional standard)
    case
        when i.pct_within_18_weeks >= 95 then 'Compliant (>=95%)'
        when i.pct_within_18_weeks >= 90 then 'Near target (90-95%)'
        when i.pct_within_18_weeks >= 80 then 'Below target (80-90%)'
        else 'Well below target (<80%)'
    end as target_compliance_category,

    -- Load metadata
    current_timestamp as model_run_at

from icb_metrics i
left join benchmarks b
    on i.period = b.period

order by i.pct_within_18_weeks desc
