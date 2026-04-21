with source as (
    select *
    from {{ source('bronze', 'carts') }}
)

select
    cast(id as bigint) as cart_id,
    cast(user_id as bigint) as user_id,
    cast(date as timestamp) as cart_created_at_utc,
    cast(null as bigint) as source_version,
    cast(_dlt_id as varchar) as _dlt_id,
    cast(_dlt_load_id as varchar) as _dlt_load_id,
    cast(_axiomatic_extracted_at_utc as timestamp) as _axiomatic_extracted_at_utc
from source
