{{
  config(
    materialized='table',
    schema=env_var('AXIOMATIC_SCHEMA_GOLD', 'gold')
  )
}}

--
-- RTT Pathway Dimension (Type 0 - fixed lookup)
-- SK=BK pattern: Business key (source code) = Surrogate key
--
-- Grain: RTT Part Type from source
-- Maps source codes to meaningful descriptions and categories
--

with pathway_types as (
    select distinct rtt_part_type
    from {{ ref('int_rtt_metrics_by_commissioner') }}
    where rtt_part_type is not null
)

select
    -- SK=BK: Source code IS the surrogate key
    rtt_part_type,

    -- Pathway description (from NHS RTT documentation)
    case rtt_part_type
        when 'Part_1A' then 'Incomplete pathways - Admitted'
        when 'Part_1B' then 'Incomplete pathways - Non-admitted'
        when 'Part_1C' then 'Incomplete pathways - Patient choice'
        when 'Part_2' then 'Completed pathways - All'
        when 'Part_2A' then 'Completed pathways - Admitted'
        when 'Part_2B' then 'Completed pathways - Non-admitted'
        when 'Part_2C' then 'Completed pathways - Patient choice'
        when 'Part_3' then 'New RTT periods - All'
        else 'Unknown pathway type'
    end as pathway_description,

    -- Pathway category for analysis grouping
    case
        when rtt_part_type like 'Part_1%' then 'Incomplete'
        when rtt_part_type like 'Part_2%' then 'Completed'
        when rtt_part_type like 'Part_3%' then 'New Periods'
        else 'Other'
    end as pathway_category,

    -- Detail level
    case
        when rtt_part_type in ('Part_1A', 'Part_1B', 'Part_1C',
                               'Part_2A', 'Part_2B', 'Part_2C') then 'Detailed'
        when rtt_part_type in ('Part_1', 'Part_2', 'Part_3') then 'Summary'
        else 'Other'
    end as detail_level,

    -- Sort order for consistent display
    case rtt_part_type
        when 'Part_1' then 1
        when 'Part_1A' then 2
        when 'Part_1B' then 3
        when 'Part_1C' then 4
        when 'Part_2' then 5
        when 'Part_2A' then 6
        when 'Part_2B' then 7
        when 'Part_2C' then 8
        when 'Part_3' then 9
        else 99
    end as display_order

from pathway_types

order by display_order
