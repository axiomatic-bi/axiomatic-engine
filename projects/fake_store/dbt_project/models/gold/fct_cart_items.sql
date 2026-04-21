with cart_lines as (
    select
        coalesce(
            cart_item_dlt_id,
            {{ dbt_utils.generate_surrogate_key(['cart_dlt_id', 'product_id', 'cart_item_index']) }}
        ) as cart_item_key,
        cart_dlt_id,
        product_id,
        quantity,
        _dlt_load_id,
        _axiomatic_extracted_at_utc
    from {{ ref('stg_carts__products') }}
),
cart_headers as (
    select
        cart_id,
        user_id,
        cart_created_at_utc,
        _dlt_id as cart_dlt_id
    from {{ ref('stg_carts') }}
),
fact_base as (
    select
        lines.cart_item_key,
        headers.cart_id,
        headers.user_id,
        lines.product_id,
        headers.cart_created_at_utc,
        lines.quantity,
        lines._dlt_load_id,
        lines._axiomatic_extracted_at_utc as as_of_extracted_at_utc
    from cart_lines as lines
    inner join cart_headers as headers
        on lines.cart_dlt_id = headers.cart_dlt_id
),
resolved_product_version as (
    select
        base.*,
        products.product_version_key,
        products.price as price_at_sale
    from fact_base as base
    left join {{ ref('dim_products') }} as products
        on base.product_id = products.product_id
       and base.as_of_extracted_at_utc >= products.valid_from_utc
       and (
            products.valid_to_utc is null
            or base.as_of_extracted_at_utc < products.valid_to_utc
       )
),
resolved_user_version as (
    select
        base.*,
        users.user_version_key
    from resolved_product_version as base
    left join {{ ref('dim_users') }} as users
        on base.user_id = users.user_id
       and users.is_current
)

select
    base.cart_item_key,
    base.cart_id,
    base.product_version_key,
    base.user_version_key,
    dates.date_key,
    base.quantity,
    base.price_at_sale,
    cast(base.quantity * base.price_at_sale as double) as line_amount,
    base.cart_created_at_utc,
    base._dlt_load_id,
    base.as_of_extracted_at_utc as _axiomatic_extracted_at_utc
from resolved_user_version as base
left join {{ ref('dim_date') }} as dates
    on cast(base.cart_created_at_utc as date) = dates.date_day
