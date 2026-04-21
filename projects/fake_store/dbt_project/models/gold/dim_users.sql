with staged as (
    select
        user_id,
        email,
        username,
        phone,
        name_firstname,
        name_lastname,
        address_city,
        address_street,
        address_number,
        address_zipcode as address_postcode,
        address_geolocation_lat,
        address_geolocation_long,
        _dlt_load_id,
        _axiomatic_extracted_at_utc,
        {{ dbt_utils.generate_surrogate_key([
            'email',
            'username',
            'phone',
            'name_firstname',
            'name_lastname',
            'address_city',
            'address_street',
            'address_number',
            'address_postcode',
            'address_geolocation_lat',
            'address_geolocation_long'
        ]) }} as attribute_hash
    from {{ ref('stg_users') }}
),
deduplicated as (
    select *
    from (
        select
            *,
            row_number() over (
                partition by user_id, _axiomatic_extracted_at_utc, attribute_hash
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
                partition by user_id
                order by _axiomatic_extracted_at_utc asc
            ) as previous_attribute_hash
        from deduplicated
    )
    where previous_attribute_hash is null
       or attribute_hash != previous_attribute_hash
),
versioned as (
    select
        user_id,
        email,
        username,
        phone,
        name_firstname,
        name_lastname,
        address_city,
        address_street,
        address_number,
        address_postcode,
        address_geolocation_lat,
        address_geolocation_long,
        attribute_hash,
        _dlt_load_id,
        _axiomatic_extracted_at_utc as valid_from_utc,
        lead(_axiomatic_extracted_at_utc) over (
            partition by user_id
            order by _axiomatic_extracted_at_utc asc
        ) as valid_to_utc
    from changes_only
)

select
    {{ dbt_utils.generate_surrogate_key(['user_id', 'valid_from_utc']) }} as user_version_key,
    user_id,
    email,
    username,
    phone,
    name_firstname,
    name_lastname,
    address_city,
    address_street,
    address_number,
    address_postcode,
    address_geolocation_lat,
    address_geolocation_long,
    valid_from_utc,
    valid_to_utc,
    valid_to_utc is null as is_current,
    attribute_hash,
    _dlt_load_id,
    valid_from_utc as _axiomatic_extracted_at_utc
from versioned
