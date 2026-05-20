{{
  config(
    materialized='view',
    schema=env_var('AXIOMATIC_SCHEMA_SILVER', 'silver')
  )
}}

--
-- Silver staging: RTT commissioner data
-- Source: dlt-ingested bronze table
-- Grain: Provider x Commissioner x RTT Part Type x Period
--
-- Performs casting and column renaming from raw NHS CSV format
--

select
    -- Period
    "Period" as period,

    -- Provider organization (where treatment happens)
    "Provider Parent Org Code" as provider_parent_org_code,
    "Provider Parent Name" as provider_parent_name,
    "Provider Org Code" as provider_org_code,
    "Provider Org Name" as provider_org_name,

    -- Commissioner organization (who pays)
    "Commissioner Parent Org Code" as commissioner_parent_org_code,
    "Commissioner Parent Name" as commissioner_parent_name,
    "Commissioner Org Code" as commissioner_org_code,
    "Commissioner Org Name" as commissioner_org_name,

    -- RTT part type (e.g., Part_1A for incomplete pathways)
    "RTT Part Type" as rtt_part_type,

    -- Week bands 0-18
    cast("0 To 1 Weeks SUM 1" as integer) as weeks_0_to_1,
    cast("1 To 2 Weeks SUM 1" as integer) as weeks_1_to_2,
    cast("2 To 3 Weeks SUM 1" as integer) as weeks_2_to_3,
    cast("3 To 4 Weeks SUM 1" as integer) as weeks_3_to_4,
    cast("4 To 5 Weeks SUM 1" as integer) as weeks_4_to_5,
    cast("5 To 6 Weeks SUM 1" as integer) as weeks_5_to_6,
    cast("6 To 7 Weeks SUM 1" as integer) as weeks_6_to_7,
    cast("7 To 8 Weeks SUM 1" as integer) as weeks_7_to_8,
    cast("8 To 9 Weeks SUM 1" as integer) as weeks_8_to_9,
    cast("9 To 10 Weeks SUM 1" as integer) as weeks_9_to_10,
    cast("10 To 11 Weeks SUM 1" as integer) as weeks_10_to_11,
    cast("11 To 12 Weeks SUM 1" as integer) as weeks_11_to_12,
    cast("12 To 13 Weeks SUM 1" as integer) as weeks_12_to_13,
    cast("13 To 14 Weeks SUM 1" as integer) as weeks_13_to_14,
    cast("14 To 15 Weeks SUM 1" as integer) as weeks_14_to_15,
    cast("15 To 16 Weeks SUM 1" as integer) as weeks_15_to_16,
    cast("16 To 17 Weeks SUM 1" as integer) as weeks_16_to_17,
    cast("17 To 18 Weeks SUM 1" as integer) as weeks_17_to_18,

    -- Week bands 18-26
    cast("Gt 18 To 19 Weeks SUM 1" as integer) as weeks_18_to_19,
    cast("Gt 19 To 20 Weeks SUM 1" as integer) as weeks_19_to_20,
    cast("Gt 20 To 21 Weeks SUM 1" as integer) as weeks_20_to_21,
    cast("Gt 21 To 22 Weeks SUM 1" as integer) as weeks_21_to_22,
    cast("Gt 22 To 23 Weeks SUM 1" as integer) as weeks_22_to_23,
    cast("Gt 23 To 24 Weeks SUM 1" as integer) as weeks_23_to_24,
    cast("Gt 24 To 25 Weeks SUM 1" as integer) as weeks_24_to_25,
    cast("Gt 25 To 26 Weeks SUM 1" as integer) as weeks_25_to_26,

    -- Week bands 26-52
    cast("Gt 26 To 27 Weeks SUM 1" as integer) as weeks_26_to_27,
    cast("Gt 27 To 28 Weeks SUM 1" as integer) as weeks_27_to_28,
    cast("Gt 28 To 29 Weeks SUM 1" as integer) as weeks_28_to_29,
    cast("Gt 29 To 30 Weeks SUM 1" as integer) as weeks_29_to_30,
    cast("Gt 30 To 31 Weeks SUM 1" as integer) as weeks_30_to_31,
    cast("Gt 31 To 32 Weeks SUM 1" as integer) as weeks_31_to_32,
    cast("Gt 32 To 33 Weeks SUM 1" as integer) as weeks_32_to_33,
    cast("Gt 33 To 34 Weeks SUM 1" as integer) as weeks_33_to_34,
    cast("Gt 34 To 35 Weeks SUM 1" as integer) as weeks_34_to_35,
    cast("Gt 35 To 36 Weeks SUM 1" as integer) as weeks_35_to_36,
    cast("Gt 36 To 37 Weeks SUM 1" as integer) as weeks_36_to_37,
    cast("Gt 37 To 38 Weeks SUM 1" as integer) as weeks_37_to_38,
    cast("Gt 38 To 39 Weeks SUM 1" as integer) as weeks_38_to_39,
    cast("Gt 39 To 40 Weeks SUM 1" as integer) as weeks_39_to_40,
    cast("Gt 40 To 41 Weeks SUM 1" as integer) as weeks_40_to_41,
    cast("Gt 41 To 42 Weeks SUM 1" as integer) as weeks_41_to_42,
    cast("Gt 42 To 43 Weeks SUM 1" as integer) as weeks_42_to_43,
    cast("Gt 43 To 44 Weeks SUM 1" as integer) as weeks_43_to_44,
    cast("Gt 44 To 45 Weeks SUM 1" as integer) as weeks_44_to_45,
    cast("Gt 45 To 46 Weeks SUM 1" as integer) as weeks_45_to_46,
    cast("Gt 46 To 47 Weeks SUM 1" as integer) as weeks_46_to_47,
    cast("Gt 47 To 48 Weeks SUM 1" as integer) as weeks_47_to_48,
    cast("Gt 48 To 49 Weeks SUM 1" as integer) as weeks_48_to_49,
    cast("Gt 49 To 50 Weeks SUM 1" as integer) as weeks_49_to_50,
    cast("Gt 50 To 51 Weeks SUM 1" as integer) as weeks_50_to_51,
    cast("Gt 51 To 52 Weeks SUM 1" as integer) as weeks_51_to_52,

    -- Week bands 52-54
    cast("Gt 52 To 53 Weeks SUM 1" as integer) as weeks_52_to_53,
    cast("Gt 53 To 54 Weeks SUM 1" as integer) as weeks_53_to_54,

    -- Week bands 54-65
    cast("Gt 54 To 55 Weeks SUM 1" as integer) as weeks_54_to_55,
    cast("Gt 55 To 56 Weeks SUM 1" as integer) as weeks_55_to_56,
    cast("Gt 56 To 57 Weeks SUM 1" as integer) as weeks_56_to_57,
    cast("Gt 57 To 58 Weeks SUM 1" as integer) as weeks_57_to_58,
    cast("Gt 58 To 59 Weeks SUM 1" as integer) as weeks_58_to_59,
    cast("Gt 59 To 60 Weeks SUM 1" as integer) as weeks_59_to_60,
    cast("Gt 60 To 61 Weeks SUM 1" as integer) as weeks_60_to_61,
    cast("Gt 61 To 62 Weeks SUM 1" as integer) as weeks_61_to_62,
    cast("Gt 62 To 63 Weeks SUM 1" as integer) as weeks_62_to_63,
    cast("Gt 63 To 64 Weeks SUM 1" as integer) as weeks_63_to_64,
    cast("Gt 64 To 65 Weeks SUM 1" as integer) as weeks_64_to_65,

    -- Week bands 65-78
    cast("Gt 65 To 66 Weeks SUM 1" as integer) as weeks_65_to_66,
    cast("Gt 66 To 67 Weeks SUM 1" as integer) as weeks_66_to_67,
    cast("Gt 67 To 68 Weeks SUM 1" as integer) as weeks_67_to_68,
    cast("Gt 68 To 69 Weeks SUM 1" as integer) as weeks_68_to_69,
    cast("Gt 69 To 70 Weeks SUM 1" as integer) as weeks_69_to_70,
    cast("Gt 70 To 71 Weeks SUM 1" as integer) as weeks_70_to_71,
    cast("Gt 71 To 72 Weeks SUM 1" as integer) as weeks_71_to_72,
    cast("Gt 72 To 73 Weeks SUM 1" as integer) as weeks_72_to_73,
    cast("Gt 73 To 74 Weeks SUM 1" as integer) as weeks_73_to_74,
    cast("Gt 74 To 75 Weeks SUM 1" as integer) as weeks_74_to_75,
    cast("Gt 75 To 76 Weeks SUM 1" as integer) as weeks_75_to_76,
    cast("Gt 76 To 77 Weeks SUM 1" as integer) as weeks_76_to_77,
    cast("Gt 77 To 78 Weeks SUM 1" as integer) as weeks_77_to_78,

    -- Week bands 78-104
    cast("Gt 78 To 79 Weeks SUM 1" as integer) as weeks_78_to_79,
    cast("Gt 79 To 80 Weeks SUM 1" as integer) as weeks_79_to_80,
    cast("Gt 80 To 81 Weeks SUM 1" as integer) as weeks_80_to_81,
    cast("Gt 81 To 82 Weeks SUM 1" as integer) as weeks_81_to_82,
    cast("Gt 82 To 83 Weeks SUM 1" as integer) as weeks_82_to_83,
    cast("Gt 83 To 84 Weeks SUM 1" as integer) as weeks_83_to_84,
    cast("Gt 84 To 85 Weeks SUM 1" as integer) as weeks_84_to_85,
    cast("Gt 85 To 86 Weeks SUM 1" as integer) as weeks_85_to_86,
    cast("Gt 86 To 87 Weeks SUM 1" as integer) as weeks_86_to_87,
    cast("Gt 87 To 88 Weeks SUM 1" as integer) as weeks_87_to_88,
    cast("Gt 88 To 89 Weeks SUM 1" as integer) as weeks_88_to_89,
    cast("Gt 89 To 90 Weeks SUM 1" as integer) as weeks_89_to_90,
    cast("Gt 90 To 91 Weeks SUM 1" as integer) as weeks_90_to_91,
    cast("Gt 91 To 92 Weeks SUM 1" as integer) as weeks_91_to_92,
    cast("Gt 92 To 93 Weeks SUM 1" as integer) as weeks_92_to_93,
    cast("Gt 93 To 94 Weeks SUM 1" as integer) as weeks_93_to_94,
    cast("Gt 94 To 95 Weeks SUM 1" as integer) as weeks_94_to_95,
    cast("Gt 95 To 96 Weeks SUM 1" as integer) as weeks_95_to_96,
    cast("Gt 96 To 97 Weeks SUM 1" as integer) as weeks_96_to_97,
    cast("Gt 97 To 98 Weeks SUM 1" as integer) as weeks_97_to_98,
    cast("Gt 98 To 99 Weeks SUM 1" as integer) as weeks_98_to_99,
    cast("Gt 99 To 100 Weeks SUM 1" as integer) as weeks_99_to_100,
    cast("Gt 100 To 101 Weeks SUM 1" as integer) as weeks_100_to_101,
    cast("Gt 101 To 102 Weeks SUM 1" as integer) as weeks_101_to_102,
    cast("Gt 102 To 103 Weeks SUM 1" as integer) as weeks_102_to_103,
    cast("Gt 103 To 104 Weeks SUM 1" as integer) as weeks_103_to_104,

    -- Week band 104+
    cast("Gt 104 Weeks SUM 1" as integer) as weeks_over_104,

    -- Canonical totals from source (trustworthy, not derived)
    cast("Total" as integer) as total_waiting_list,
    cast("Total All" as integer) as total_all_count,

    -- Metadata
    _dlt_load_id as load_id,
    _dlt_id as record_id

from {{ source('nhs_rtt_bronze_ingest', 'rtt_commissioner_mar25') }}
