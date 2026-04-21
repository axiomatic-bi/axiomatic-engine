with cart_items as (
    select *
    from {{ source('bronze', 'carts__products') }}
),
carts as (
    select
        _dlt_id,
        _dlt_load_id,
        _axiomatic_extracted_at_utc
    from {{ ref('stg_carts') }}
)

select
    cast(cart_items._dlt_id as varchar) as cart_item_dlt_id,
    cast(cart_items._dlt_parent_id as varchar) as cart_dlt_id,
    cast(carts._dlt_load_id as varchar) as _dlt_load_id,
    cast(cart_items._dlt_list_idx as bigint) as cart_item_index,
    cast(cart_items.product_id as bigint) as product_id,
    cast(cart_items.quantity as bigint) as quantity,
    carts._axiomatic_extracted_at_utc as _axiomatic_extracted_at_utc
from cart_items
left join carts
    on cart_items._dlt_parent_id = carts._dlt_id
