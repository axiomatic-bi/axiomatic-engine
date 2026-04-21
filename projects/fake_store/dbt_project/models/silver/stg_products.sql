with source as (
    select *
    from {{ source('bronze', 'products') }}
)

select
    cast(id as bigint) as product_id,
    cast(title as varchar) as title,
    cast(description as varchar) as description,
    cast(category as varchar) as category,
    cast(image as varchar) as image,
    cast(price as double) as price,
    cast(rating__rate as double) as rating_rate,
    cast(rating__count as bigint) as rating_count,
    cast(_dlt_id as varchar) as _dlt_id,
    cast(_dlt_load_id as varchar) as _dlt_load_id,
    cast(_axiomatic_extracted_at_utc as timestamp) as _axiomatic_extracted_at_utc
from source
