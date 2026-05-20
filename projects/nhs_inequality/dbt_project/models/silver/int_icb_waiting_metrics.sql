{{
  config(
    materialized='view',
    schema=env_var('AXIOMATIC_SCHEMA_SILVER', 'silver')
  )
}}

--
-- ICB-level waiting time metrics
-- Aggregated from commissioner-level data
-- Grain: ICB x Period
--
-- Identifies ICBs by checking commissioner_org_code length (3 chars = ICB)
-- and commissioner_parent_org_code patterns (QE* = ICBs)
--

select
    period,

    -- ICB identification
    commissioner_org_code as icb_code,
    commissioner_org_name as icb_name,
    commissioner_parent_org_code as icb_parent_code,
    commissioner_parent_name as icb_parent_name,

    -- Aggregate metrics (sum across all RTT part types)
    sum(total_waiting_list) as total_waiting_list,
    sum(total_waiting_list - count_over_18_weeks) as total_within_18_weeks,
    sum(count_over_18_weeks) as total_over_18_weeks,
    sum(count_over_52_weeks) as total_over_52_weeks,
    sum(count_over_65_weeks) as total_over_65_weeks,
    sum(count_over_78_weeks) as total_over_78_weeks,
    sum(count_over_104_weeks) as total_over_104_weeks,

    -- Calculated percentages (using ICB-level totals as denominator)
    case
        when sum(total_waiting_list) > 0
        then round(100.0 * sum(total_waiting_list - count_over_18_weeks) / sum(total_waiting_list), 2)
        else 0
    end as pct_within_18_weeks,

    case
        when sum(total_waiting_list) > 0
        then round(100.0 * sum(count_over_18_weeks) / sum(total_waiting_list), 2)
        else 0
    end as pct_over_18_weeks,

    case
        when sum(total_waiting_list) > 0
        then round(100.0 * sum(count_over_52_weeks) / sum(total_waiting_list), 2)
        else 0
    end as pct_over_52_weeks,

    case
        when sum(total_waiting_list) > 0
        then round(100.0 * sum(count_over_65_weeks) / sum(total_waiting_list), 2)
        else 0
    end as pct_over_65_weeks,

    case
        when sum(total_waiting_list) > 0
        then round(100.0 * sum(count_over_78_weeks) / sum(total_waiting_list), 2)
        else 0
    end as pct_over_78_weeks,

    case
        when sum(total_waiting_list) > 0
        then round(100.0 * sum(count_over_104_weeks) / sum(total_waiting_list), 2)
        else 0
    end as pct_over_104_weeks,

    -- Flag for England-level records (parent org is NHS England)
    case
        when commissioner_parent_org_code is null
          or commissioner_parent_org_code = ''
          or upper(commissioner_parent_org_code) like 'X%'
        then true
        else false
    end as is_england_level,

    -- Flag for regional level (parent is NHS England region)
    case
        when commissioner_parent_org_code like 'Y%'
          or commissioner_org_code like 'Y%'
        then true
        else false
    end as is_regional_level

from {{ ref('int_rtt_metrics_by_commissioner') }}

where commissioner_org_code is not null
  and commissioner_org_code != ''

-- Filter to ICB-level records (3-character codes typically)
  and length(trim(commissioner_org_code)) = 3

group by
    period,
    commissioner_org_code,
    commissioner_org_name,
    commissioner_parent_org_code,
    commissioner_parent_name

having sum(total_waiting_list) > 0
-- Exclude ICBs with no reported patients: prevents division-by-zero in downstream
-- percentage calculations and suppresses empty submissions (e.g. non-reporting months)
