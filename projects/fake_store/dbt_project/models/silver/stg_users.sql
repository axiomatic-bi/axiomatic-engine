with source as (
    select *
    from {{ source('bronze', 'users') }}
)

select
    cast(id as bigint) as user_id,
    cast(email as varchar) as email,
    cast(username as varchar) as username,
    cast(phone as varchar) as phone,
    cast(name__firstname as varchar) as name_firstname,
    cast(name__lastname as varchar) as name_lastname,
    cast(address__city as varchar) as address_city,
    cast(address__street as varchar) as address_street,
    cast(address__number as bigint) as address_number,
    cast(address__zipcode as varchar) as address_zipcode,
    cast(address__geolocation__lat as double) as address_geolocation_lat,
    cast(address__geolocation__long as double) as address_geolocation_long,
    cast(_dlt_id as varchar) as _dlt_id,
    cast(_dlt_load_id as varchar) as _dlt_load_id,
    cast(_axiomatic_extracted_at_utc as timestamp) as _axiomatic_extracted_at_utc
from source
