{{
  config(
    materialized='view',
    schema=env_var('AXIOMATIC_SCHEMA_SILVER', 'silver')
  )
}}

--
-- ICB benchmarks: Official England and regional totals from source
-- Grain: Period x Level (England/Region)
--
-- Extracts TRUE NHS England/region aggregates (not calculated peer averages)
-- Naming honesty: england_* = official source totals, never peer averages
--

with england_totals as (
    -- England-level records: null/empty parent or 'X%' pattern
    select
        period,
        'England' as level_type,
        'ENG' as level_code,
        'NHS England' as level_name,

        sum(total_waiting_list) as england_total_waiting_list,
        sum(total_waiting_list - count_over_18_weeks) as england_total_within_18_weeks,
        sum(count_over_18_weeks) as england_total_over_18_weeks,
        sum(count_over_52_weeks) as england_total_over_52_weeks,
        sum(count_over_65_weeks) as england_total_over_65_weeks,
        sum(count_over_78_weeks) as england_total_over_78_weeks,
        sum(count_over_104_weeks) as england_total_over_104_weeks,

        round(100.0 * sum(total_waiting_list - count_over_18_weeks) / nullif(sum(total_waiting_list), 0), 2)
            as england_pct_within_18_weeks,
        round(100.0 * sum(count_over_18_weeks) / nullif(sum(total_waiting_list), 0), 2)
            as england_pct_over_18_weeks,
        round(100.0 * sum(count_over_52_weeks) / nullif(sum(total_waiting_list), 0), 2)
            as england_pct_over_52_weeks,
        round(100.0 * sum(count_over_65_weeks) / nullif(sum(total_waiting_list), 0), 2)
            as england_pct_over_65_weeks,
        round(100.0 * sum(count_over_78_weeks) / nullif(sum(total_waiting_list), 0), 2)
            as england_pct_over_78_weeks,
        round(100.0 * sum(count_over_104_weeks) / nullif(sum(total_waiting_list), 0), 2)
            as england_pct_over_104_weeks

    from {{ ref('int_rtt_metrics_by_commissioner') }}

    where commissioner_parent_org_code is null
       or commissioner_parent_org_code = ''
       or upper(commissioner_parent_org_code) like 'X%'
       or upper(commissioner_org_code) like 'X%'

    group by period
),

regional_totals as (
    -- Regional-level records: 'Y%' pattern
    select
        period,
        'Region' as level_type,
        commissioner_org_code as level_code,
        commissioner_org_name as level_name,
        commissioner_parent_org_code as region_parent_code,

        sum(total_waiting_list) as region_total_waiting_list,
        sum(total_waiting_list - count_over_18_weeks) as region_total_within_18_weeks,
        sum(count_over_18_weeks) as region_total_over_18_weeks,
        sum(count_over_52_weeks) as region_total_over_52_weeks,
        sum(count_over_65_weeks) as region_total_over_65_weeks,
        sum(count_over_78_weeks) as region_total_over_78_weeks,
        sum(count_over_104_weeks) as region_total_over_104_weeks,

        round(100.0 * sum(total_waiting_list - count_over_18_weeks) / nullif(sum(total_waiting_list), 0), 2)
            as region_pct_within_18_weeks,
        round(100.0 * sum(count_over_18_weeks) / nullif(sum(total_waiting_list), 0), 2)
            as region_pct_over_18_weeks,
        round(100.0 * sum(count_over_52_weeks) / nullif(sum(total_waiting_list), 0), 2)
            as region_pct_over_52_weeks,
        round(100.0 * sum(count_over_65_weeks) / nullif(sum(total_waiting_list), 0), 2)
            as region_pct_over_65_weeks,
        round(100.0 * sum(count_over_78_weeks) / nullif(sum(total_waiting_list), 0), 2)
            as region_pct_over_78_weeks,
        round(100.0 * sum(count_over_104_weeks) / nullif(sum(total_waiting_list), 0), 2)
            as region_pct_over_104_weeks

    from {{ ref('int_rtt_metrics_by_commissioner') }}

    where commissioner_org_code like 'Y%'
       or commissioner_parent_org_code like 'Y%'

    group by
        period,
        commissioner_org_code,
        commissioner_org_name,
        commissioner_parent_org_code
)

-- Combine England and regional benchmarks
select
    period,
    level_type,
    level_code,
    level_name,

    -- Raw totals
    england_total_waiting_list,
    england_total_within_18_weeks,
    england_total_over_18_weeks,
    england_total_over_52_weeks,
    england_total_over_65_weeks,
    england_total_over_78_weeks,
    england_total_over_104_weeks,

    -- Percentages
    england_pct_within_18_weeks,
    england_pct_over_18_weeks,
    england_pct_over_52_weeks,
    england_pct_over_65_weeks,
    england_pct_over_78_weeks,
    england_pct_over_104_weeks,

    -- Region fields (null for England rows)
    cast(null as varchar) as region_parent_code,
    cast(null as bigint) as region_total_waiting_list,
    cast(null as bigint) as region_total_within_18_weeks,
    cast(null as bigint) as region_total_over_18_weeks,
    cast(null as bigint) as region_total_over_52_weeks,
    cast(null as bigint) as region_total_over_65_weeks,
    cast(null as bigint) as region_total_over_78_weeks,
    cast(null as bigint) as region_total_over_104_weeks,
    cast(null as decimal(10,2)) as region_pct_within_18_weeks,
    cast(null as decimal(10,2)) as region_pct_over_18_weeks,
    cast(null as decimal(10,2)) as region_pct_over_52_weeks,
    cast(null as decimal(10,2)) as region_pct_over_65_weeks,
    cast(null as decimal(10,2)) as region_pct_over_78_weeks,
    cast(null as decimal(10,2)) as region_pct_over_104_weeks

from england_totals

union all

select
    period,
    level_type,
    level_code,
    level_name,

    -- England fields (null for region rows)
    cast(null as bigint) as england_total_waiting_list,
    cast(null as bigint) as england_total_within_18_weeks,
    cast(null as bigint) as england_total_over_18_weeks,
    cast(null as bigint) as england_total_over_52_weeks,
    cast(null as bigint) as england_total_over_65_weeks,
    cast(null as bigint) as england_total_over_78_weeks,
    cast(null as bigint) as england_total_over_104_weeks,
    cast(null as decimal(10,2)) as england_pct_within_18_weeks,
    cast(null as decimal(10,2)) as england_pct_over_18_weeks,
    cast(null as decimal(10,2)) as england_pct_over_52_weeks,
    cast(null as decimal(10,2)) as england_pct_over_65_weeks,
    cast(null as decimal(10,2)) as england_pct_over_78_weeks,
    cast(null as decimal(10,2)) as england_pct_over_104_weeks,

    -- Region fields
    region_parent_code,
    region_total_waiting_list,
    region_total_within_18_weeks,
    region_total_over_18_weeks,
    region_total_over_52_weeks,
    region_total_over_65_weeks,
    region_total_over_78_weeks,
    region_total_over_104_weeks,
    region_pct_within_18_weeks,
    region_pct_over_18_weeks,
    region_pct_over_52_weeks,
    region_pct_over_65_weeks,
    region_pct_over_78_weeks,
    region_pct_over_104_weeks

from regional_totals
