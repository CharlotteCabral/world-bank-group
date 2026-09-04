select distinct
    {{ dbt_utils.generate_surrogate_key(['country_iso3']) }} as country_key,
    country_iso3,
    country_code,
    country_name
from {{ ref('stg_world_bank') }}
where country_iso3 is not null