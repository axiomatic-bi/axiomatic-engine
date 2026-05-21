{{
  config(
    materialized='view',
    schema=env_var('AXIOMATIC_SCHEMA_SILVER', 'silver')
  )
}}

--
-- RTT metrics calculated at commissioner grain
-- Source: Bronze staged RTT data
-- Grain: Commissioner Org x RTT Part Type
--
-- Uses source total_count as canonical denominator.
-- Derives breach metrics by summing all relevant week bands.
--

select
    period,

    -- Commissioner organisation (who pays)
    commissioner_org_code,
    commissioner_org_name,
    commissioner_parent_org_code,
    commissioner_parent_name,

    -- RTT part type (e.g., Part_1A for incomplete pathways)
    rtt_part_type,

    -- Canonical totals from source (not derived)
    total_count as total_waiting_list,
    total_all_count,

    -- Derived breach metrics: patients waiting 18+ weeks
    ({{ count_over_18_weeks() }}) as count_over_18_weeks,

    -- Derived: patients waiting 52+ weeks
    ({{ count_over_52_weeks() }}) as count_over_52_weeks,

    -- Derived: patients waiting 65+ weeks (NHS improvement target)
    ({{ count_over_65_weeks() }}) as count_over_65_weeks,

    -- Derived: patients waiting 78+ weeks (NHS 78-week pledge)
    ({{ count_over_78_weeks() }}) as count_over_78_weeks,

    -- Derived: patients waiting 104+ weeks (extreme long waiters)
    coalesce(cast(weeks_over_104 as integer), 0) as count_over_104_weeks,

    -- Percentage calculations (using canonical total_count as denominator)
    case
        when total_count > 0
        then round(100.0 * ({{ count_over_18_weeks() }}) / total_count, 2)
        else 0
    end as pct_over_18_weeks,

    case
        when total_count > 0
        then round(100.0 * ({{ count_over_52_weeks() }}) / total_count, 2)
        else 0
    end as pct_over_52_weeks,

    -- Metadata
    load_id,
    record_id

from {{ ref('stg_rtt_commissioner') }}

where total_count is not null
