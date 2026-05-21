{{
  config(
    materialized='table',
    schema=env_var('AXIOMATIC_SCHEMA_GOLD', 'gold')
  )
}}

--
-- ICB Dimension (Type 1 - overwrite on changes)
-- SK=BK pattern: Business key = Surrogate key (stable, meaningful identifier)
--
-- Grain: ICB (3-character codes)
-- Extension ready for v1.1 deprivation enrichment via business key join
--

with icb_data as (
    -- Extract ICB-level records from commissioner data
    select distinct
        commissioner_org_code as icb_code,
        commissioner_org_name as icb_name,
        commissioner_parent_org_code as region_code,
        commissioner_parent_name as region_name

    from {{ ref('int_rtt_metrics_by_commissioner') }}

    where commissioner_org_code is not null
      and commissioner_org_code != ''

      -- ICB-level: 3-character codes (QE* pattern typically)
      and length(trim(commissioner_org_code)) = 3

      -- Exclude England-level rows (X* pattern)
      and not (upper(commissioner_org_code) like 'X%')

      -- Exclude regional rows (Y* pattern)
      and not (commissioner_org_code like 'Y%')
      and not (commissioner_parent_org_code like 'Y%')
)

select
    -- SK=BK: Business key IS the surrogate key
    icb_code,

    -- Attributes
    icb_name,
    region_code,
    region_name,

    -- Organisation level classification (all ICB-level in this dimension)
    'ICB' as org_level,

    -- v1.1 Extension points (null for now, ready for IMD enrichment)
    cast(null as decimal(10,4)) as avg_imd_score,
    cast(null as integer) as imd_decile_mode,
    cast(null as varchar) as deprivation_quintile,
    cast(null as integer) as population

from icb_data

order by icb_code
