with staged as (
    select
        product_id,
        title,
        description,
        category,
        image,
        price,
        rating_rate,
        rating_count,
        _dlt_load_id,
        _axiomatic_extracted_at_utc,
        {{ dbt_utils.generate_surrogate_key([
            'title',
            'description',
            'category',
            'image',
            'price',
            'rating_rate',
            'rating_count'
        ]) }} as attribute_hash
    from {{ ref('stg_products') }}
),
deduplicated as (
    select *
    from (
        select
            *,
            row_number() over (
                partition by product_id, _axiomatic_extracted_at_utc, attribute_hash
                order by _dlt_load_id desc
            ) as row_num
        from staged
    )
    where row_num = 1
),
changes_only as (
    select *
    from (
        select
            *,
            lag(attribute_hash) over (
                partition by product_id
                order by _axiomatic_extracted_at_utc asc
            ) as previous_attribute_hash
        from deduplicated
    )
    where previous_attribute_hash is null
       or attribute_hash != previous_attribute_hash
),
versioned as (
    select
        product_id,
        title,
        description,
        category,
        image,
        price,
        rating_rate,
        rating_count,
        attribute_hash,
        _dlt_load_id,
        _axiomatic_extracted_at_utc as valid_from_utc,
        lead(_axiomatic_extracted_at_utc) over (
            partition by product_id
            order by _axiomatic_extracted_at_utc asc
        ) as valid_to_utc
    from changes_only
)

select
    {{ dbt_utils.generate_surrogate_key(['product_id', 'valid_from_utc']) }} as product_version_key,
    product_id,
    title,
    description,
    category,
    image,
    price,
    rating_rate,
    rating_count,
    valid_from_utc,
    valid_to_utc,
    valid_to_utc is null as is_current,
    attribute_hash,
    _dlt_load_id,
    valid_from_utc as _axiomatic_extracted_at_utc
from versioned
