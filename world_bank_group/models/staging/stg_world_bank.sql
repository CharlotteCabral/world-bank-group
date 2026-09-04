
select
    surrogate_key,
    `hash`,
    inserted_at,
    json_extract_scalar(payload, '$.countryiso3code') as country_iso3,
    json_extract_scalar(payload, '$.country.value') as country_name,
    json_extract_scalar(payload, '$.country.id') as country_code,
    json_extract_scalar(payload, '$.indicator.id') as indicator_id,
    json_extract_scalar(payload, '$.indicator.value') as indicator_name,
    cast(json_extract_scalar(payload, '$.date') as int64) as annee,
    cast(json_extract_scalar(payload, '$.value') as float64) as valeur,
    json_extract_scalar(payload, '$.unit') as unit
from {{ source('world_bank_raw', 'raw_data') }}

