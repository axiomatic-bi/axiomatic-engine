{{
  config(
    materialized='table',
    schema=env_var('AXIOMATIC_SCHEMA_GOLD', 'gold')
  )
}}

--
-- Period Dimension (Type 0 - fixed attributes)
-- SK=BK pattern: Business key (date value) = Surrogate key
--
-- Grain: Reporting period (monthly from source)
-- NHS Fiscal Year: April - March
--

with periods as (
    select distinct period
    from {{ ref('int_rtt_metrics_by_commissioner') }}
    where period is not null
),

parsed as (
    select
        period,

        -- Parse period assuming format like '2025-03' or 'Mar 2025'
        -- Handle various formats that might appear in source
        case
            when period like '%-%' then
                -- ISO format: 2025-03 or 2025-03-31
                cast(split_part(period, '-', 1) as integer)
            when period like '%/%' then
                -- US format: 03/2025
                cast(split_part(period, '/', 2) as integer)
            else
                -- Try to extract 4-digit year
                cast(substring(period from '\d{4}') as integer)
        end as period_year,

        case
            when period like '%-%' then
                cast(split_part(period, '-', 2) as integer)
            when period like '%/%' then
                cast(split_part(period, '/', 1) as integer)
            else
                null
        end as period_month,

        -- Quarter (calendar)
        case
            when cast(split_part(period, '-', 2) as integer) between 1 and 3 then 1
            when cast(split_part(period, '-', 2) as integer) between 4 and 6 then 2
            when cast(split_part(period, '-', 2) as integer) between 7 and 9 then 3
            when cast(split_part(period, '-', 2) as integer) between 10 and 12 then 4
            else null
        end as period_quarter

    from periods
)

select
    -- SK=BK: The period value IS the surrogate key
    period,

    -- Calendar attributes
    period_year,
    period_month,
    period_quarter,

    -- Quarter name
    'Q' || cast(period_quarter as varchar) as quarter_name,

    -- NHS Fiscal Year (April - March)
    -- FY starts in April, so Jan-Mar of year Y = FY(Y-1), Apr-Dec of year Y = FY(Y)
    case
        when period_month >= 4 then period_year
        else period_year - 1
    end as fiscal_year,

    -- Fiscal quarter
    case
        when period_month in (4, 5, 6) then 1
        when period_month in (7, 8, 9) then 2
        when period_month in (10, 11, 12) then 3
        when period_month in (1, 2, 3) then 4
        else null
    end as fiscal_quarter,

    -- Period as date (first of month) for time-based calculations
    cast(period || '-01' as date) as period_date

from parsed

where period_year is not null
  and period_month is not null

order by period
