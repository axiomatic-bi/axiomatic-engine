with cart_dates as (
    select distinct
        cast(cart_created_at_utc as date) as date_day
    from {{ ref('stg_carts') }}
    where cart_created_at_utc is not null
)

select
    cast(strftime(date_day, '%Y%m%d') as bigint) as date_key,
    date_day,
    extract(year from date_day) as year_number,
    extract(quarter from date_day) as quarter_number,
    extract(month from date_day) as month_number,
    strftime(date_day, '%B') as month_name,
    extract(day from date_day) as day_of_month,
    cast(strftime(date_day, '%w') as integer) as day_of_week_number,
    strftime(date_day, '%A') as day_of_week_name,
    cast(strftime(date_day, '%w') as integer) in (0, 6) as is_weekend
from cart_dates
