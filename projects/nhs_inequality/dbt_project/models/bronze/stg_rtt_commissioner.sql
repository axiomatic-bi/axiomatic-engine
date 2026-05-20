{{
  config(
    materialized='view',
    schema=env_var('AXIOMATIC_SCHEMA_BRONZE', 'bronze')
  )
}}

--
-- Staged RTT waiting times data
-- Source: NHS England RTT waiting times (full extract)
-- Grain: Provider x Commissioner x RTT Part Type x Period
--
-- Note: This full extract contains both provider and commissioner context,
-- allowing analysis at either grain. Commissioner fields show which organisation
-- commissioned the activity.
--

select
    -- Period
    "Period" as period,

    -- Provider organisation (where treatment happens)
    "Provider Parent Org Code" as provider_parent_org_code,
    "Provider Parent Name" as provider_parent_name,
    "Provider Org Code" as provider_org_code,
    "Provider Org Name" as provider_org_name,

    -- Commissioner organisation (who pays)
    "Commissioner Parent Org Code" as commissioner_parent_org_code,
    "Commissioner Parent Name" as commissioner_parent_name,
    "Commissioner Org Code" as commissioner_org_code,
    "Commissioner Org Name" as commissioner_org_name,

    -- RTT part type (e.g., Part_1A for incomplete pathways)
    "RTT Part Type" as rtt_part_type,

    -- Key waiting time buckets
    "0 To 1 Weeks SUM 1" as weeks_0_to_1,
    "1 To 2 Weeks SUM 1" as weeks_1_to_2,
    "2 To 3 Weeks SUM 1" as weeks_2_to_3,
    "3 To 4 Weeks SUM 1" as weeks_3_to_4,
    "4 To 5 Weeks SUM 1" as weeks_4_to_5,
    "5 To 6 Weeks SUM 1" as weeks_5_to_6,
    "6 To 7 Weeks SUM 1" as weeks_6_to_7,
    "7 To 8 Weeks SUM 1" as weeks_7_to_8,
    "8 To 9 Weeks SUM 1" as weeks_8_to_9,
    "9 To 10 Weeks SUM 1" as weeks_9_to_10,
    "10 To 11 Weeks SUM 1" as weeks_10_to_11,
    "11 To 12 Weeks SUM 1" as weeks_11_to_12,
    "12 To 13 Weeks SUM 1" as weeks_12_to_13,
    "13 To 14 Weeks SUM 1" as weeks_13_to_14,
    "14 To 15 Weeks SUM 1" as weeks_14_to_15,
    "15 To 16 Weeks SUM 1" as weeks_15_to_16,
    "16 To 17 Weeks SUM 1" as weeks_16_to_17,
    "17 To 18 Weeks SUM 1" as weeks_17_to_18,

    -- 18+ weeks (target breach)
    "Gt 18 To 19 Weeks SUM 1" as weeks_18_to_19,
    "Gt 19 To 20 Weeks SUM 1" as weeks_19_to_20,
    "Gt 20 To 21 Weeks SUM 1" as weeks_20_to_21,
    "Gt 21 To 22 Weeks SUM 1" as weeks_21_to_22,
    "Gt 22 To 23 Weeks SUM 1" as weeks_22_to_23,
    "Gt 23 To 24 Weeks SUM 1" as weeks_23_to_24,
    "Gt 24 To 25 Weeks SUM 1" as weeks_24_to_25,
    "Gt 25 To 26 Weeks SUM 1" as weeks_25_to_26,

    -- 52+ weeks (long waiters)
    "Gt 52 To 53 Weeks SUM 1" as weeks_52_to_53,
    "Gt 53 To 54 Weeks SUM 1" as weeks_53_to_54,
    -- ... (truncated for brevity, full model has all week bands)

    -- Totals
    "Total" as total_count,
    "Total All" as total_all_count,

    -- Load metadata
    _dlt_load_id as load_id,
    _dlt_id as record_id

from {{ source('nhs_rtt_bronze_ingest', 'rtt_commissioner_mar25') }}
