with source as (
    select *
    from {{ source('bronze', 'users') }}
)

select
    cast(id as bigint) as user_id,
    cast(email as varchar) as email,
    cast(username as varchar) as username,
    cast(phone as varchar) as phone,
    {{ to_title_case('name__firstname') }} as name_firstname,
    {{ to_title_case('name__lastname') }} as name_lastname,
    {{ to_title_case('address__city') }} as address_city,
    {{ to_title_case('address__street') }} as address_street,
    cast(address__number as bigint) as address_number,
    cast(address__zipcode as varchar) as address_zipcode,
    cast(address__geolocation__lat as double) as address_geolocation_lat,
    cast(address__geolocation__long as double) as address_geolocation_long,
    cast(_dlt_id as varchar) as _dlt_id,
    cast(_dlt_load_id as varchar) as _dlt_load_id,
    cast(_axiomatic_extracted_at_utc as timestamp) as _axiomatic_extracted_at_utc
from source
