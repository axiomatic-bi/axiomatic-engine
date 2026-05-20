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

england_metrics as (
    select
        period,
        avg(pct_within_18_weeks) as england_avg_pct_within_18_weeks,
        max(pct_within_18_weeks) as england_max_pct_within_18_weeks,
        min(pct_within_18_weeks) as england_min_pct_within_18_weeks,
        sum(total_within_18_weeks) as england_total_within_18_weeks,
        sum(total_waiting_list) as england_total_waiting_list,
        round(100.0 * sum(total_within_18_weeks) / nullif(sum(total_waiting_list), 0), 2)
            as england_overall_pct_within_18_weeks,
        avg(pct_over_52_weeks) as england_avg_pct_over_52_weeks,
        sum(total_over_52_weeks) as england_total_over_52_weeks,
        avg(pct_over_65_weeks) as england_avg_pct_over_65_weeks,
        sum(total_over_65_weeks) as england_total_over_65_weeks,
        avg(pct_over_78_weeks) as england_avg_pct_over_78_weeks,
        sum(total_over_78_weeks) as england_total_over_78_weeks,
        avg(pct_over_104_weeks) as england_avg_pct_over_104_weeks,
        sum(total_over_104_weeks) as england_total_over_104_weeks
    from {{ ref('int_icb_waiting_metrics') }}
    where not is_england_level
      and not is_regional_level
    group by period
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

    -- England benchmarks
    e.england_overall_pct_within_18_weeks as england_18wk_target_pct,
    e.england_avg_pct_within_18_weeks as england_avg_icb_18wk_pct,
    e.england_max_pct_within_18_weeks as england_best_icb_18wk_pct,
    e.england_min_pct_within_18_weeks as england_worst_icb_18wk_pct,
    e.england_total_over_52_weeks as england_total_long_waiters,
    e.england_total_over_65_weeks as england_total_over_65_weeks,
    e.england_total_over_78_weeks as england_total_over_78_weeks,
    e.england_total_over_104_weeks as england_total_over_104_weeks,

    -- Variance from England target
    round(i.pct_within_18_weeks - e.england_overall_pct_within_18_weeks, 2)
        as variance_from_england_target,

    -- Performance vs England (for ranking)
    case
        when i.pct_within_18_weeks >= e.england_overall_pct_within_18_weeks
        then 'At or above England average'
        when i.pct_within_18_weeks >= e.england_overall_pct_within_18_weeks - 5
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
left join england_metrics e
    on i.period = e.period

order by i.pct_within_18_weeks desc
